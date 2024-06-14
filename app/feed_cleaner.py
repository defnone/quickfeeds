import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from app.models import User, FeedItem, Feed
from app import db


def clean_old_feed_items(user, app):
    """
    Cleans old feed items for a specific user based on user settings.

    Args:
        user (User): The user whose feed items need to be cleaned.
        app (Flask): The Flask application context to use.
    """
    with app.app_context():
        logging.info(
            "Starting clean up of old feed items for user %s", user.username
        )
        try:
            cleanup_interval_days = user.settings.clean_after_days or 365
            cutoff_date = datetime.now() - timedelta(
                days=cleanup_interval_days
            )
            logging.info(
                "Cleanup interval days: %d, Cutoff date: %s",
                cleanup_interval_days,
                cutoff_date,
            )

            feeds = (
                db.session.query(Feed).filter(Feed.user_id == user.id).all()
            )
            for feed in feeds:
                old_items = (
                    db.session.query(FeedItem)
                    .filter(
                        FeedItem.feed_id == feed.id,
                        FeedItem.pub_date < cutoff_date,
                        FeedItem.favourite == False,
                    )
                    .all()
                )

                logging.info(
                    "Found %d old items for feed %d", len(old_items), feed.id
                )
                for item in old_items:
                    logging.debug(
                        'Deleting feed item "%s" with pub_date %s',
                        item.title,
                        item.pub_date,
                    )
                    db.session.delete(item)

            db.session.commit()
            logging.info(
                "Old feed items cleaned up for user %s", user.username
            )
        except SQLAlchemyError as e:
            logging.error("Database error: %s", e, exc_info=True)
            db.session.rollback()
        except Exception as e:
            logging.error("Unhandled exception: %s", e, exc_info=True)


def clean_feeds(app):
    """
    This function cleans the feeds for all users.
    Args:
        app (Flask): The Flask application context to use.
    """
    with app.app_context():
        logging.info("Starting feed clean up thread")
        try:
            users = db.session.query(User).all()
            if not users:
                logging.info("No users found.")
                return

            for user in users:
                if not hasattr(user, "id"):
                    logging.error(
                        "User is missing 'id' attribute. Check User model."
                    )
                    continue

                clean_old_feed_items(user, app)

        except SQLAlchemyError as e:
            logging.error("Database error: %s", e, exc_info=True)
            db.session.rollback()
        except Exception as e:
            logging.error("Unhandled exception: %s", e, exc_info=True)
