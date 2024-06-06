import time
import logging
from datetime import datetime, timedelta
import feedparser
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models import User, Feed, FeedItem
from app import db, create_app
from app.utils.cleaner import clean_summary

app = create_app()


def update_feeds_thread():
    with app.app_context():
        logging.info("Starting feed update thread")

        while True:
            try:
                user = db.session.query(User).first()
                if not user:
                    logging.info(
                        "User not found. Checking again in 60 seconds."
                    )
                    time.sleep(60)
                    continue

                if not hasattr(user, "id"):
                    logging.error(
                        "User is missing 'id' attribute. Check User model."
                    )
                    time.sleep(60)
                    continue

                last_sync = user.last_sync or datetime.min
                update_interval = timedelta(
                    minutes=user.settings.update_interval
                )

                if datetime.now() - last_sync >= update_interval:
                    logging.info("Updating feeds for user %s", user.username)
                    start_time = time.time()  # Начало измерения времени
                    update_user_feeds(user)
                    user.last_sync = datetime.now()
                    db.session.commit()
                    end_time = time.time()  # Конец измерения времени
                    elapsed_time = end_time - start_time
                    logging.info(
                        "Feeds updated for user %s in %.2f seconds",
                        user.username,
                        elapsed_time,
                    )

                next_update_time = (
                    last_sync + update_interval
                ) - datetime.now()
                sleep_time = max(next_update_time.total_seconds(), 1)
                logging.info(
                    "Waiting %d seconds until next update", sleep_time
                )
                time.sleep(sleep_time)

            except SQLAlchemyError as e:
                logging.error("Database error: %s", e, exc_info=True)
                db.session.rollback()
                time.sleep(60)
            except Exception as e:
                logging.error("Unhandled exception: %s", e, exc_info=True)
                time.sleep(60)


def update_user_feeds(user):
    feeds = db.session.query(Feed).filter_by(user_id=user.id).all()
    if not feeds:
        logging.info("User %s has no feeds to update", user.username)
        return

    for feed in feeds:
        if not hasattr(feed, "id"):
            logging.error("Feed is missing 'id' attribute. Check Feed model.")
            continue
        update_feed(feed, user)


def update_feed(feed, user):
    logging.info("Updating feed %s", feed.title)
    feed_data = feedparser.parse(feed.url, sanitize_html=False)
    entries = feed_data.entries

    for entry in entries:
        with db.session.no_autoflush:
            existing_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            if existing_item:
                logging.debug(
                    "Item with link %s already exists, skipping", entry.link
                )
                continue

            creator = entry.get("author") or (
                entry.get("authors")[0]["name"]
                if entry.get("authors")
                else None
            )
            pub_date = datetime(*entry.published_parsed[:6])

            enclosure_html = ""
            if "enclosures" in entry:
                for enclosure in entry.enclosures:
                    url = enclosure.get("url")
                    type_ = enclosure.get("type")

                    if type_ and url:
                        if type_.startswith("image/"):
                            enclosure_html += (
                                f'<img src="{url}" alt="Enclosure Image">'
                            )
                        elif type_.startswith("audio/"):
                            enclosure_html += (
                                f'<audio controls src="{url}"></audio>'
                            )
                        elif type_.startswith("video/"):
                            enclosure_html += (
                                f'<video controls src="{url}"></video>'
                            )
            # Handle media content in the feed entry
            media_content_html = ""
            if "media_content" in entry:

                for media_content in entry.media_content:
                    url = media_content.get("url")
                    medium = media_content.get("medium")

                    if url and medium == "image":
                        media_content_html += f'<img src="{url}">'
                        break

            summary = media_content_html + enclosure_html + entry.summary
            summary = clean_summary(summary)

            guid = entry.get("id") or entry.get("guid") or entry.link
            new_item = FeedItem(
                title=entry.title,
                link=entry.link,
                pub_date=pub_date,
                summary=summary,
                guid=guid,
                feed_id=feed.id,
                creator=creator,
            )
            try:
                db.session.add(new_item)
                db.session.commit()
                logging.info("New feed item added: %s", new_item.title)
            except IntegrityError as e:
                db.session.rollback()
                logging.warning(
                    "Duplicate found for link %s: %s", entry.link, e
                )
            except SQLAlchemyError as e:
                db.session.rollback()
                logging.error("Error adding feed item: %s", e)
