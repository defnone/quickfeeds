from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pytest
import time
from sqlalchemy.orm import declarative_base
from app.models import User, Feed, FeedItem, Settings
from app.feed_updater import (
    update_feeds_thread,
    update_user_feeds,
    update_feed,
)
from app import db, create_app

Base = declarative_base()


# Fixture for creating the application context
@pytest.fixture
def app():
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# Fixture for getting the test client
@pytest.fixture
def client(app):
    return app.test_client()


# Fixture for creating a test user
@pytest.fixture
def user(app):
    user = User(
        username="testuser",
        password="testpassword",
        last_sync=datetime.now() - timedelta(days=1),
    )
    db.session.add(user)
    db.session.commit()
    settings = Settings(user_id=user.id, update_interval=10)
    db.session.add(settings)
    db.session.commit()
    user.settings = settings
    db.session.add(user)
    db.session.commit()
    return user


# Fixture for creating a test feed
@pytest.fixture
def feed(user):
    feed = Feed(title="Test Feed", url="http://test.feed/rss", user_id=user.id)
    db.session.add(feed)
    db.session.commit()
    return feed


# Fixture for creating a second test feed
@pytest.fixture
def second_feed(user):
    feed = Feed(
        title="Second Test Feed",
        url="http://second.test.feed/rss",
        user_id=user.id,
    )
    db.session.add(feed)
    db.session.commit()
    return feed


# Fixture for mocking the sleep function
@pytest.fixture
def mock_sleep(mocker):
    mocker.patch("time.sleep", return_value=None)


# Test case for update_feeds_thread function with no users
def test_update_feeds_thread_no_user(app, mock_sleep):
    with patch("app.feed_updater.db.session.query") as mock_query:
        mock_query.return_value.first.return_value = None
        with patch(
            "app.feed_updater.time.sleep", side_effect=KeyboardInterrupt
        ) as sleep_mock:
            try:
                update_feeds_thread()
            except KeyboardInterrupt:
                pass
            sleep_mock.assert_called_with(60)


# Test case for update_feeds_thread function with a user but no feeds
def test_update_feeds_thread_with_user_no_feeds(app, user, mock_sleep):
    with patch("app.feed_updater.db.session.query") as mock_query:
        mock_query.return_value.first.return_value = user
        with patch(
            "app.feed_updater.update_user_feeds"
        ) as mock_update_user_feeds:
            with patch(
                "app.feed_updater.time.sleep", side_effect=KeyboardInterrupt
            ):
                try:
                    update_feeds_thread()
                except KeyboardInterrupt:
                    pass
                mock_update_user_feeds.assert_called_once_with(user)


# Test case for update_user_feeds function with no feeds
def test_update_user_feeds_no_feeds(app, user):
    with patch("app.feed_updater.db.session.query") as mock_query:
        mock_query.return_value.filter_by.return_value.all.return_value = []
        update_user_feeds(user)
        mock_query.return_value.filter_by.assert_called_with(user_id=user.id)


# Test case for update_user_feeds function with multiple feeds
def test_update_user_feeds_with_feeds(app, user, feed, second_feed):
    with patch("app.feed_updater.update_feed") as mock_update_feed:
        update_user_feeds(user)
        assert mock_update_feed.call_count == 2


# Test case for update_feed function with no entries
def test_update_feed_no_entries(app, feed):
    with patch(
        "app.feed_updater.feedparser.parse", return_value=MagicMock(entries=[])
    ):
        with patch.object(
            db.session.query(FeedItem).filter_by(
                link="http://test.feed/item1"
            ),
            "first",
            return_value=None,
        ) as mock_filter_by:
            update_feed(feed, feed.user)
            mock_filter_by.assert_not_called()


# Test case for update_feed function with entries
def test_update_feed_with_entries(app, feed, mocker):
    entry = MagicMock()
    entry.link = "http://test.feed/item1"
    entry.title = "Test Entry"
    entry.summary = "Test Summary"
    entry.published_parsed = time.gmtime()
    entry.id = "test-id"
    entry.get.side_effect = lambda x: "Test Creator" if x == "author" else None

    parsed_feed = MagicMock(entries=[entry])

    with patch("app.feed_updater.feedparser.parse", return_value=parsed_feed):
        with patch(
            "app.feed_updater.clean_summary", return_value="Cleaned Summary"
        ):
            update_feed(feed, feed.user)
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.title == "Test Entry"
            assert feed_item.summary == "Cleaned Summary"
            assert feed_item.guid == "http://test.feed/item1"
            assert feed_item.creator == "Test Creator"


# Test case for update_feed function with a duplicate entry
def test_update_feed_with_duplicate_entry(app, feed, mocker):
    entry = MagicMock()
    entry.link = "http://test.feed/item1"
    entry.title = "Test Entry"
    entry.summary = "Test Summary"
    entry.published_parsed = time.gmtime()
    entry.id = "test-id"
    entry.get.side_effect = lambda x: "Test Creator" if x == "author" else None

    parsed_feed = MagicMock(entries=[entry])

    with patch("app.feed_updater.feedparser.parse", return_value=parsed_feed):
        with patch(
            "app.feed_updater.clean_summary", return_value="Cleaned Summary"
        ):
            existing_item = FeedItem(
                title="Existing Entry",
                link=entry.link,
                pub_date=datetime.now(),
                summary="Existing Summary",
                guid=entry.id,
                feed_id=feed.id,
                creator="Existing Creator",
            )
            db.session.add(existing_item)
            db.session.commit()

            update_feed(feed, feed.user)
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.title == "Existing Entry"


# Test case for update_feed function with different entry formats
def test_update_feed_with_different_entry_format(app, feed, mocker):
    # First test case: using updated_parsed
    entry = MagicMock()
    entry.link = "http://test.feed/item1"
    entry.title = "Test Entry"
    entry.summary = "Test Summary"
    entry.updated_parsed = (
        2024,
        6,
        8,
        14,
        41,
        49,
    )  # Explicitly defined updated_parsed data
    entry.id = "test-id"
    entry.get.side_effect = lambda x: None

    parsed_feed = MagicMock(entries=[entry])

    with patch("app.feed_updater.feedparser.parse", return_value=parsed_feed):
        with patch(
            "app.feed_updater.clean_summary", return_value="Cleaned Summary"
        ):
            with patch("app.feed_updater.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2024, 6, 8, 14, 41, 49
                )
                mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                    *args, **kwargs
                )
                update_feed(feed, feed.user)
                feed_item = (
                    db.session.query(FeedItem)
                    .filter_by(link=entry.link)
                    .first()
                )
                assert feed_item is not None
                assert feed_item.title == "Test Entry"
                assert feed_item.summary == "Cleaned Summary"
                assert feed_item.guid == "http://test.feed/item1"
                assert feed_item.creator is None
                assert feed_item.pub_date == datetime(*entry.updated_parsed)

    # Second test case: no published_parsed and updated_parsed
    entry_no_date = MagicMock()
    entry_no_date.link = "http://test.feed/item2"
    entry_no_date.title = "Test Entry No Date"
    entry_no_date.summary = "Test Summary No Date"
    entry_no_date.id = "test-id-no-date"
    entry_no_date.get.side_effect = lambda x: None

    parsed_feed_no_date = MagicMock(entries=[entry_no_date])

    with patch(
        "app.feed_updater.feedparser.parse", return_value=parsed_feed_no_date
    ):
        with patch(
            "app.feed_updater.clean_summary", return_value="Cleaned Summary"
        ):
            with patch("app.feed_updater.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(
                    2024, 6, 8, 14, 41, 49
                )
                mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                    *args, **kwargs
                )
                update_feed(feed, feed.user)
                feed_item_no_date = (
                    db.session.query(FeedItem)
                    .filter_by(link=entry_no_date.link)
                    .first()
                )
                assert feed_item_no_date is not None
                assert feed_item_no_date.title == "Test Entry No Date"
                assert feed_item_no_date.summary == "Cleaned Summary"
                assert feed_item_no_date.guid == "http://test.feed/item2"
                assert feed_item_no_date.creator is None
                assert (
                    feed_item_no_date.pub_date
                    == mock_datetime.now.return_value
                )


# Test case for update_feed function with attachments
def test_update_feed_with_attachments(app, feed, mocker):
    entry = MagicMock()
    entry.link = "http://test.feed/item1"
    entry.title = "Test Entry"
    entry.summary = "Test Summary"
    entry.published_parsed = time.gmtime()
    entry.id = "test-id"
    entry.get.side_effect = lambda x: None

    entry.enclosures = [
        {"url": "http://test.feed/image.jpg", "type": "image/jpeg"},
        {"url": "http://test.feed/audio.mp3", "type": "audio/mpeg"},
    ]

    parsed_feed = MagicMock(entries=[entry])

    with patch("app.feed_updater.feedparser.parse", return_value=parsed_feed):
        with patch(
            "app.feed_updater.clean_summary",
            return_value=(
                '<img src="http://test.feed/image.jpg" alt="Enclosure Image">'
                '<audio controls src="http://test.feed/audio.mp3"></audio>'
                "Cleaned Summary"
            ),
        ):
            update_feed(feed, feed.user)
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.summary == (
                '<img src="http://test.feed/image.jpg" alt="Enclosure Image">'
                '<audio controls src="http://test.feed/audio.mp3"></audio>'
                "Cleaned Summary"
            )


# Test case for update_feed function with media content
def test_update_feed_with_media_content(app, feed, mocker):
    entry = MagicMock()
    entry.link = "http://test.feed/item1"
    entry.title = "Test Entry"
    entry.summary = "Test Summary"
    entry.published_parsed = time.gmtime()
    entry.id = "test-id"
    entry.get.side_effect = lambda x: None

    entry.media_content = [
        {"url": "http://test.feed/media.jpg", "medium": "image"},
    ]

    parsed_feed = MagicMock(entries=[entry])

    with patch("app.feed_updater.feedparser.parse", return_value=parsed_feed):
        with patch(
            "app.feed_updater.clean_summary",
            return_value=(
                '<img src="http://test.feed/media.jpg">' "Cleaned Summary"
            ),
        ):
            update_feed(feed, feed.user)
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.summary == (
                '<img src="http://test.feed/media.jpg">' "Cleaned Summary"
            )
