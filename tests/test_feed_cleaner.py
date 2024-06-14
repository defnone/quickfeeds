import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from app.models import User, Feed, FeedItem, Settings
from app import db, create_app
from app.feed_cleaner import clean_old_feed_items, clean_feeds
import logging


# Fixture to create the application for testing
@pytest.fixture
def app():
    app = create_app(config_name="testing")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# Fixture to create the test client
@pytest.fixture
def client(app):
    return app.test_client()


# Fixture to create a test user
@pytest.fixture
def user(app):
    user = User(username="testuser", password="testpassword")
    db.session.add(user)
    db.session.commit()
    settings = Settings(user_id=user.id, clean_after_days=10)
    db.session.add(settings)
    db.session.commit()
    user.settings = settings
    db.session.add(user)
    db.session.commit()
    return user


# Fixture to create a test feed and feed items
@pytest.fixture
def feed_and_items(app, user):
    feed = Feed(user_id=user.id, url="https://example.com/feed")
    db.session.add(feed)
    db.session.commit()

    old_item = FeedItem(
        feed_id=feed.id,
        title="Old Item",
        pub_date=datetime.now() - timedelta(days=20),
        favourite=False,
        link="https://example.com/old_item",
    )
    new_item = FeedItem(
        feed_id=feed.id,
        title="New Item",
        pub_date=datetime.now(),
        favourite=False,
        link="https://example.com/new_item",
    )
    favourite_item = FeedItem(
        feed_id=feed.id,
        title="Favourite Item",
        pub_date=datetime.now() - timedelta(days=20),
        favourite=True,
        link="https://example.com/favourite_item",
    )

    db.session.add_all([old_item, new_item, favourite_item])
    db.session.commit()
    return feed, [old_item, new_item, favourite_item]


# Test for the clean_old_feed_items function
def test_clean_old_feed_items(app, user, feed_and_items):
    feed, items = feed_and_items

    with app.app_context():
        clean_old_feed_items(user, app)

        remaining_items = (
            db.session.query(FeedItem)
            .filter(FeedItem.feed_id == feed.id)
            .all()
        )
        remaining_titles = [item.title for item in remaining_items]

        logging.info(f"Remaining items: {remaining_titles}")

        # Ensure that the old item is deleted, but the new and favourite items remain
        assert "Old Item" not in remaining_titles
        assert "New Item" in remaining_titles
        assert "Favourite Item" in remaining_titles


# Test for the clean_feeds function
def test_clean_feeds(app, user, feed_and_items):
    feed, items = feed_and_items

    with app.app_context():
        clean_feeds(app)

        remaining_items = (
            db.session.query(FeedItem)
            .filter(FeedItem.feed_id == feed.id)
            .all()
        )
        remaining_titles = [item.title for item in remaining_items]

        logging.info(f"Remaining items: {remaining_titles}")

        # Ensure that the old item is deleted, but the new and favourite items remain
        assert "Old Item" not in remaining_titles
        assert "New Item" in remaining_titles
        assert "Favourite Item" in remaining_titles


# Test for database error in clean_old_feed_items
def test_clean_old_feed_items_db_error(app, user, feed_and_items, mocker):
    # Mocking db.session.commit to raise SQLAlchemyError
    mocker.patch(
        "app.feed_cleaner.db.session.commit", side_effect=SQLAlchemyError
    )

    with app.app_context():
        clean_old_feed_items(user, app)

        remaining_items = (
            db.session.query(FeedItem)
            .filter(FeedItem.feed_id == feed_and_items[0].id)
            .all()
        )
        remaining_titles = [item.title for item in remaining_items]

        # Ensure no items are deleted due to the database error
        assert "Old Item" in remaining_titles
        assert "New Item" in remaining_titles
        assert "Favourite Item" in remaining_titles


# Test for unhandled exception in clean_feeds
def test_clean_feeds_unhandled_exception(app, user, feed_and_items, mocker):
    # Mocking clean_old_feed_items to raise a generic Exception
    mocker.patch(
        "app.feed_cleaner.clean_old_feed_items",
        side_effect=Exception("Unhandled exception"),
    )

    with app.app_context():
        clean_feeds(app)

        remaining_items = (
            db.session.query(FeedItem)
            .filter(FeedItem.feed_id == feed_and_items[0].id)
            .all()
        )
        remaining_titles = [item.title for item in remaining_items]

        # Ensure no items are deleted due to the unhandled exception
        assert "Old Item" in remaining_titles
        assert "New Item" in remaining_titles
        assert "Favourite Item" in remaining_titles
