import logging
from datetime import datetime, timedelta, UTC
import time
import http.client
import feedparser
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pytz import timezone as pytz_timezone
from app.models import User, Feed, FeedItem
from app import db, create_app
from app.utils.cleaner import clean_summary

app = create_app()


def update_user_feeds(user):
    user_timezone = pytz_timezone(user.settings.timezone)
    feeds = db.session.query(Feed).filter_by(user_id=user.id).all()
    if not feeds:
        logging.info("User %s has no feeds to update", user.username)
        return

    for feed in feeds:
        if not hasattr(feed, "id"):
            logging.error("Feed is missing 'id' attribute. Check Feed model.")
            continue
        update_feed(feed, user, user_timezone)


def update_feed(feed, user, user_timezone):
    logging.info("Updating feed %s", feed.title)
    try:
        feed_data = feedparser.parse(feed.url, sanitize_html=False)
    except http.client.RemoteDisconnected:
        logging.error(
            "Failed to update feed %s due to connection issues. Moving on to the next feed.",
            feed.url,
        )
        return
    entries = feed_data.entries
    clean_after_date = datetime.now(user_timezone) - timedelta(
        days=user.settings.clean_after_days - 1
    )

    for entry in entries:
        with db.session.no_autoflush:
            existing_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            if existing_item:
                continue

            creator = entry.get("author") or (
                entry.get("authors")[0]["name"]
                if entry.get("authors")
                else None
            )

            try:
                if hasattr(entry, "published_parsed"):
                    pub_date = datetime(
                        *entry.published_parsed[:6], tzinfo=user_timezone
                    )
                elif hasattr(entry, "updated_parsed"):
                    pub_date = datetime(
                        *entry.updated_parsed[:6], tzinfo=user_timezone
                    )
                else:
                    pub_date = datetime.now(user_timezone)
                    logging.warning(
                        "Entry is missing 'published_parsed' and 'updated_parsed' attributes. Using current date and time."
                    )
            except Exception:
                pub_date = datetime.now(user_timezone)
                logging.warning(
                    "Error parsing date for entry %s. Using current date and time.",
                    entry.link,
                )

            if pub_date < clean_after_date:
                # logging.debug(
                #     "Skipping entry %s as it is older than %d days",
                #     entry.link,
                #     user.settings.clean_after_days,
                # )
                continue

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

            media_content_html = ""
            if "media_content" in entry:
                for media_content in entry.media_content:
                    url = media_content.get("url")
                    type_ = media_content.get("type")
                    medium = media_content.get("medium")
                    if url and (
                        medium == "image" or type_.startswith("image/")
                    ):
                        media_content_html += f'<img src="{url}">'
                        break

            media_thumbnail_html = ""
            if "media_thumbnail" in entry:
                for media_thumbnail in entry.media_thumbnail:
                    url = media_thumbnail.get("url")
                    width = media_thumbnail.get("width")
                    height = media_thumbnail.get("height")
                    if url:
                        media_content_html += f'<img src="{url}" width="{width}" height="{height}">'
                        break

            summary = ""
            if "content" in entry and len(entry["content"][0]["value"]) > 0:
                summary = entry["content"][0]["value"]
            elif "description" in entry:
                summary = entry["description"]
            elif "summary" in entry:
                summary = entry["summary"]
            else:
                summary = ""

            summary = (
                media_thumbnail_html
                + media_content_html
                + enclosure_html
                + summary
            )
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


def update_feeds_thread(app=app):
    with app.app_context():
        logging.info("Starting feed update thread")
        try:
            user = db.session.query(User).first()
            if not user:
                logging.info("User not found.")
                return

            if not hasattr(user, "id"):
                logging.error(
                    "User is missing 'id' attribute. Check User model."
                )
                return

            now = datetime.now(UTC)

            logging.info("Updating feeds for user %s", user.username)
            start_time = time.time()
            update_user_feeds(user)
            user.last_sync = now
            db.session.commit()
            end_time = time.time()
            elapsed_time = end_time - start_time
            logging.info(
                "Feeds updated for user %s in %.2f seconds",
                user.username,
                elapsed_time,
            )
        except SQLAlchemyError as e:
            logging.error("Database error: %s", e, exc_info=True)
            db.session.rollback()
        except Exception as e:
            logging.error("Unhandled exception: %s", e, exc_info=True)
