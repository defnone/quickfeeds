import tempfile
from datetime import datetime, timedelta
import pytest
import feedparser
from app.models import User, Settings, FeedItem
from app.routes.add_feed import is_feed
from app import db, create_app

# A valid RSS feed for testing
VALID_RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example RSS Feed</title>
    <description>This is an example of an RSS feed</description>
    <link>http://www.example.com/</link>
    <item>
      <title>Example entry 1</title>
      <link>http://www.example.com/example-entry-1</link>
      <description>This is an example entry 1</description>
    </item>
    <item>
      <title>Example entry 2</title>
      <link>http://www.example.com/example-entry-2</link>
      <description>This is an example entry 2</description>
    </item>
  </channel>
</rss>"""


# Test for the is_feed function with a valid feed using a temporary file
def test_is_feed_valid_feed():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as temp_file:
        temp_file.write(VALID_RSS_FEED.encode("utf-8"))
        temp_file.flush()

        result = is_feed(temp_file.name)

    print(f"Result of is_feed: {result}")
    assert result is True


# Test for the is_feed function with an invalid RSS feed
def test_is_feed_invalid_feed(mocker):
    invalid_feed = feedparser.util.FeedParserDict(
        bozo=True,
        bozo_exception=Exception("Invalid feed"),
        entries=[],
        feed={},
    )
    mocker.patch("feedparser.parse", return_value=invalid_feed)
    result = is_feed("http://invalid.feed/rss")
    assert result is False


# Test for the is_feed function with a feed that has no entries
def test_is_feed_no_entries(mocker):
    no_entries_feed = feedparser.util.FeedParserDict(
        bozo=False, entries=[], feed={}
    )
    mocker.patch("feedparser.parse", return_value=no_entries_feed)
    result = is_feed("http://no.entries/feed/rss")
    assert result is False


# Fixture for creating the app for testing
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


# Fixture for creating the test client
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


# Fixture for handling user authentication actions
@pytest.fixture
def auth(client):
    return AuthActions(client)


class AuthActions:
    def __init__(self, client):
        self.client = client

    def login(self, username="testuser", password="testpassword"):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
        )

    def logout(self):
        return self.client.get("/logout")


# Fixture to create a test user via the register endpoint
@pytest.fixture
def create_user(client):
    """Fixture to create a test user."""
    response = client.post(
        "/register", data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code in (200, 302)


# Test for the add_feed function with a valid feed, mocking is_feed and feedfinder2
def test_add_feed_valid_feed(client, auth, create_user, mocker):
    with client.application.app_context():
        auth.login()

        mocker.patch("app.routes.add_feed.is_feed", return_value=True)
        mocker.patch(
            "feedfinder2.find_feeds", return_value=["https://example.com/feed"]
        )
        mocker.patch(
            "feedparser.parse",
            return_value=feedparser.util.FeedParserDict(
                bozo=False,
                entries=[
                    feedparser.util.FeedParserDict(
                        title="Example entry 1",
                        link="https://example.com/entry-1",
                        summary="This is an example entry 1",
                        published_parsed=datetime(
                            2022, 1, 1, 0, 0, 0
                        ).timetuple(),
                    ),
                    feedparser.util.FeedParserDict(
                        title="Example entry 2",
                        link="https://example.com/entry-2",
                        summary="This is an example entry 2",
                        published_parsed=datetime(
                            2022, 1, 2, 0, 0, 0
                        ).timetuple(),
                    ),
                ],
                feed=feedparser.util.FeedParserDict(
                    title="Example RSS Feed",
                    description="This is an example RSS feed",
                    link="https://www.example.com/",
                ),
            ),
        )

        data = {
            "site_url": "https://example.com/",
            "category": "Test Category",
        }

        response = client.post("/add_feed", data=data, follow_redirects=True)

        print(f"Response status: {response.status}")
        print(f"Response location: {response.location}")
        print(f"Response data: {response.data.decode('utf-8')}")

        json_data = response.get_json()
        print(f"Response JSON: {json_data}")

        assert response.status_code == 200
        assert json_data["success"] is True


# Test for the add_feed function with an invalid feed
def test_add_feed_invalid_feed(client, auth, create_user, mocker):
    with client.application.app_context():
        auth.login()

        mocker.patch("app.routes.add_feed.is_feed", return_value=False)
        mocker.patch("feedfinder2.find_feeds", return_value=[])

        data = {
            "site_url": "http://invalid.com/rss",
            "category": "Test Category",
        }

        response = client.post("/add_feed", data=data, follow_redirects=True)

        print(f"Response status: {response.status}")
        print(f"Response location: {response.location}")
        print(f"Response data: {response.data.decode('utf-8')}")

        json_data = response.get_json()
        print(f"Response JSON: {json_data}")

        assert response.status_code == 200
        assert json_data["success"] is False
        assert "error" in json_data


# Test for the add_feed function handling media content in feed entries
def test_add_feed_with_media_content(client, auth, create_user, mocker):
    with client.application.app_context():
        auth.login()

        mocker.patch("app.routes.add_feed.is_feed", return_value=True)
        mocker.patch(
            "feedfinder2.find_feeds", return_value=["https://example.com/feed"]
        )
        mocker.patch(
            "feedparser.parse",
            return_value=feedparser.util.FeedParserDict(
                bozo=False,
                entries=[
                    feedparser.util.FeedParserDict(
                        title="Example entry with media",
                        link="https://example.com/entry-media",
                        summary="This is an example entry with media",
                        published_parsed=datetime(
                            2022, 1, 1, 0, 0, 0
                        ).timetuple(),
                        media_content=[
                            {
                                "url": "https://example.com/media.jpg",
                                "medium": "image",
                            }
                        ],
                    )
                ],
                feed=feedparser.util.FeedParserDict(
                    title="Example RSS Feed with Media",
                    description="This is an example RSS feed with media",
                    link="https://www.example.com/",
                ),
            ),
        )

        data = {
            "site_url": "https://example.com/",
            "category": "Test Category",
        }

        response = client.post("/add_feed", data=data, follow_redirects=True)

        print(f"Response status: {response.status}")
        print(f"Response location: {response.location}")
        print(f"Response data: {response.data.decode('utf-8')}")

        json_data = response.get_json()
        print(f"Response JSON: {json_data}")

        assert response.status_code == 200
        assert json_data["success"] is True

        # Verify the feed item has media content
        feed_item = FeedItem.query.filter_by(
            link="https://example.com/entry-media"
        ).first()
        assert feed_item is not None
        assert '<img src="https://example.com/media.jpg"' in feed_item.summary


# Test for the add_feed function without handling media content
def test_add_feed_without_media_content(client, auth, create_user, mocker):
    with client.application.app_context():
        auth.login()

        mocker.patch("app.routes.add_feed.is_feed", return_value=True)
        mocker.patch(
            "feedfinder2.find_feeds", return_value=["https://example.com/feed"]
        )
        mocker.patch(
            "feedparser.parse",
            return_value=feedparser.util.FeedParserDict(
                bozo=False,
                entries=[
                    feedparser.util.FeedParserDict(
                        title="Example entry without media",
                        link="https://example.com/entry-no-media",
                        summary="This is an example entry without media",
                        published_parsed=datetime(
                            2022, 1, 1, 0, 0, 0
                        ).timetuple(),
                        media_content=[],
                    )
                ],
                feed=feedparser.util.FeedParserDict(
                    title="Example RSS Feed without Media",
                    description="This is an example RSS feed without media",
                    link="https://www.example.com/",
                ),
            ),
        )

        data = {
            "site_url": "https://example.com/",
            "category": "Test Category",
        }

        response = client.post("/add_feed", data=data, follow_redirects=True)

        print(f"Response status: {response.status}")
        print(f"Response location: {response.location}")
        print(f"Response data: {response.data.decode('utf-8')}")

        json_data = response.get_json()
        print(f"Response JSON: {json_data}")

        assert response.status_code == 200
        assert json_data["success"] is True

        # Verify the feed item does not have media content
        feed_item = FeedItem.query.filter_by(
            link="https://example.com/entry-no-media"
        ).first()
        assert feed_item is not None
        assert (
            '<img src="https://example.com/media.jpg">'
            not in feed_item.summary
        )
