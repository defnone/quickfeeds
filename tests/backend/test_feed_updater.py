from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import time
import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base
from pytz import timezone as pytz_timezone
from app.models import User, Feed, FeedItem, Settings
from app.feed_updater import (
    update_feeds_thread,
    update_user_feeds,
    update_feed,
)
from app import db, create_app

Base = declarative_base()


# Pytest fixture for creating a test app with an in-memory database
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


# Pytest fixture for creating a test client for the app
@pytest.fixture
def client(app):
    return app.test_client()


# Pytest fixture for creating a test user and related settings
@pytest.fixture
def user(app):
    user = User(
        username="testuser",
        password="testpassword",
        last_sync=datetime.now() - timedelta(days=1),
    )
    db.session.add(user)
    db.session.commit()
    settings = Settings(
        user_id=user.id,
        update_interval=10,
        clean_after_days=30,
        timezone="UTC",
    )
    db.session.add(settings)
    db.session.commit()
    user.settings = settings
    db.session.add(user)
    db.session.commit()
    return user


# Pytest fixture for creating a test feed
@pytest.fixture
def feed(user):
    feed = Feed(title="Test Feed", url="http://test.feed/rss", user_id=user.id)
    db.session.add(feed)
    db.session.commit()
    return feed


# Pytest fixture for creating a second test feed
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


# Test case for updating feeds thread when no user is found
def test_update_feeds_thread_no_user(app):
    with patch("app.feed_updater.db.session.query") as mock_query:
        mock_query.return_value.first.return_value = None
        update_feeds_thread()


# Test case for updating user feeds when no feeds are found
def test_update_user_feeds_no_feeds(app, user):
    with patch("app.feed_updater.db.session.query") as mock_query:
        mock_query.return_value.filter_by.return_value.all.return_value = []
        update_user_feeds(user)
        mock_query.return_value.filter_by.assert_called_with(user_id=user.id)


# Test case for updating user feeds when feeds are present
def test_update_user_feeds_with_feeds(app, user, feed, second_feed):
    with patch("app.feed_updater.update_feed") as mock_update_feed:
        update_user_feeds(user)
        assert mock_update_feed.call_count == 2


# Test case for updating feed with no entries
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
            update_feed(feed, feed.user, pytz_timezone("UTC"))
            mock_filter_by.assert_not_called()


# Test case for updating feed with entries
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
            update_feed(feed, feed.user, pytz_timezone("UTC"))
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.title == "Test Entry"
            assert feed_item.summary == "Cleaned Summary"
            assert feed_item.guid == "http://test.feed/item1"
            assert feed_item.creator == "Test Creator"


# Test case for updating feed with duplicate entries
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

            update_feed(feed, feed.user, pytz_timezone("UTC"))
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.title == "Existing Entry"


# Test case for updating feed with a different entry format
def test_update_feed_with_different_entry_format(app, feed, mocker):
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
    )
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
                update_feed(feed, feed.user, pytz_timezone("UTC"))
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
                update_feed(feed, feed.user, pytz_timezone("UTC"))
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


# Test case for updating feed with attachments
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
            update_feed(feed, feed.user, pytz_timezone("UTC"))
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.summary == (
                '<img src="http://test.feed/image.jpg" alt="Enclosure Image">'
                '<audio controls src="http://test.feed/audio.mp3"></audio>'
                "Cleaned Summary"
            )


# Test case for updating feed with image enclosure
def test_update_feed_with_image_enclosure(app, feed, mocker):
    entry = MagicMock()
    entry.link = "http://test.feed/item1"
    entry.title = "Test Entry with Image"
    entry.summary = "Test Summary with Image"
    entry.published_parsed = time.gmtime()
    entry.id = "test-id"
    entry.get.side_effect = lambda x: None

    entry.enclosures = [
        {"url": "http://test.feed/image.jpg", "type": "image/jpeg"}
    ]

    parsed_feed = MagicMock(entries=[entry])

    with patch("app.feed_updater.feedparser.parse", return_value=parsed_feed):
        with patch(
            "app.feed_updater.clean_summary",
            return_value=(
                '<img src="http://test.feed/image.jpg" alt="Enclosure Image">'
                "Cleaned Summary"
            ),
        ):
            update_feed(feed, feed.user, pytz_timezone("UTC"))
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.summary == (
                '<img src="http://test.feed/image.jpg" alt="Enclosure Image">'
                "Cleaned Summary"
            )


# Test case for updating feed with audio enclosure
def test_update_feed_with_audio_enclosure(app, feed, mocker):
    entry = MagicMock()
    entry.link = "http://test.feed/item2"
    entry.title = "Test Entry with Audio"
    entry.summary = "Test Summary with Audio"
    entry.published_parsed = time.gmtime()
    entry.id = "test-id-2"
    entry.get.side_effect = lambda x: None

    entry.enclosures = [
        {"url": "http://test.feed/audio.mp3", "type": "audio/mpeg"}
    ]

    parsed_feed = MagicMock(entries=[entry])

    with patch("app.feed_updater.feedparser.parse", return_value=parsed_feed):
        with patch(
            "app.feed_updater.clean_summary",
            return_value=(
                '<audio controls src="http://test.feed/audio.mp3"></audio>'
                "Cleaned Summary"
            ),
        ):
            update_feed(feed, feed.user, pytz_timezone("UTC"))
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.summary == (
                '<audio controls src="http://test.feed/audio.mp3"></audio>'
                "Cleaned Summary"
            )


# Test case for updating feed with video enclosure
def test_update_feed_with_video_enclosure(app, feed, mocker):
    entry = MagicMock()
    entry.link = "http://test.feed/item3"
    entry.title = "Test Entry with Video"
    entry.summary = "Test Summary with Video"
    entry.published_parsed = time.gmtime()
    entry.id = "test-id-3"
    entry.get.side_effect = lambda x: None

    entry.enclosures = [
        {"url": "http://test.feed/video.mp4", "type": "video/mp4"}
    ]

    parsed_feed = MagicMock(entries=[entry])

    with patch("app.feed_updater.feedparser.parse", return_value=parsed_feed):
        with patch(
            "app.feed_updater.clean_summary",
            return_value=(
                '<video controls src="http://test.feed/video.mp4"></video>'
                "Cleaned Summary"
            ),
        ):
            update_feed(feed, feed.user, pytz_timezone("UTC"))
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.summary == (
                '<video controls src="http://test.feed/video.mp4"></video>'
                "Cleaned Summary"
            )


# Test case for updating feed with media content
def test_update_feed_with_media_content(app, feed, mocker):
    entry = MagicMock()
    entry.link = "http://test.feed/item4"
    entry.title = "Test Entry with Media Content"
    entry.summary = "Test Summary with Media Content"
    entry.published_parsed = time.gmtime()
    entry.id = "test-id-4"
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
            update_feed(feed, feed.user, pytz_timezone("UTC"))
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.summary == (
                '<img src="http://test.feed/media.jpg">' "Cleaned Summary"
            )


# Test case for updating feed with a fallback summary
def test_update_feed_with_fallback_summary(app, feed, mocker):
    entry = MagicMock()
    entry.link = "http://test.feed/item5"
    entry.title = "Test Entry with Fallback Summary"
    entry.description = "Test Description"
    entry.published_parsed = time.gmtime()
    entry.id = "test-id-5"
    entry.get.side_effect = lambda x: None

    parsed_feed = MagicMock(entries=[entry])

    with patch("app.feed_updater.feedparser.parse", return_value=parsed_feed):
        with patch(
            "app.feed_updater.clean_summary", return_value="Cleaned Summary"
        ):
            update_feed(feed, feed.user, pytz_timezone("UTC"))
            feed_item = (
                db.session.query(FeedItem).filter_by(link=entry.link).first()
            )
            assert feed_item is not None
            assert feed_item.summary == "Cleaned Summary"


# Test case for logging user not found in update feeds thread
def test_update_feeds_thread_user_not_found(app):
    with patch("app.feed_updater.db.session.query") as mock_query:
        mock_query.return_value.first.return_value = None
        with patch("app.feed_updater.logging.info") as mock_logging_info:
            update_feeds_thread()
            mock_logging_info.assert_any_call("User not found.")


# Test case for logging error when user is missing ID attribute
def test_update_feeds_thread_user_missing_id(app, user):
    with patch("app.feed_updater.db.session.query") as mock_query:
        user_without_id = MagicMock()
        del user_without_id.id
        mock_query.return_value.first.return_value = user_without_id
        with patch("app.feed_updater.logging.error") as mock_logging_error:
            update_feeds_thread()
            mock_logging_error.assert_any_call(
                "User is missing 'id' attribute. Check User model."
            )
