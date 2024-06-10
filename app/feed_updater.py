import time
import http.client
import logging
from datetime import datetime, timedelta
import feedparser
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models import User, Feed, FeedItem
from app import db, create_app
from app.utils.cleaner import clean_summary

app = create_app()


def update_feeds_thread():
    """
    This function continuously updates the feeds for the users.
    It runs in a loop, checking for new feed items at regular intervals,
    and updating the database with new items.
    """
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

                # Check if the update interval has passed
                if datetime.now() - last_sync >= update_interval:
                    logging.info("Updating feeds for user %s", user.username)
                    start_time = time.time()  # Start measuring time
                    update_user_feeds(user)
                    user.last_sync = datetime.now()
                    db.session.commit()
                    end_time = time.time()  # End measuring time
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
    """
    Update feeds for a specific user.

    Args:
        user (User): The user whose feeds need to be updated.
    """
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
    """
    Update a specific feed for a user.

    Args:
        feed (Feed): The feed to be updated.
        user (User): The user who owns the feed.
    """
    logging.info("Updating feed %s", feed.title)

    try:
        feed_data = feedparser.parse(feed.url, sanitize_html=False)
    except http.client.RemoteDisconnected:
        logging.error(
            "Failed to update feed %s due to connection issues. \
                Moving on to the next feed.",
            feed.url,
        )
        return
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

            try:
                if hasattr(entry, "published_parsed"):
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed"):
                    pub_date = datetime(*entry.updated_parsed[:6])
                else:
                    pub_date = datetime.now()
                    logging.warning(
                        "Entry is missing 'published_parsed' and \
                            'updated_parsed' attributes. Using \
                                current date and time."
                    )
            except Exception:
                pub_date = datetime.now()
                logging.warning(
                    "Error parsing date for entry %s. \
                        Using current date and time.",
                    entry.link,
                )

            # Handle enclosures in the feed entry
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

            if entry.get("content"):
                entry_content = entry.content[0].value
                summary += entry_content

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
