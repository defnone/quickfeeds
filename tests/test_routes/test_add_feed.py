import pytest
from flask import url_for
from app.models import Category, Feed, FeedItem
from werkzeug.security import generate_password_hash
from app import db


class MockFeed:
    """A mock class to simulate a feed."""

    def __init__(self):
        self.feed = {"title": "Test Feed"}
        self.entries = [MockEntry()]


class MockEntry:
    """A mock class to simulate a feed entry."""

    def __init__(self):
        self.title = "Test Entry"
        self.link = "http://example.com/entry"
        self.summary = "Test summary"
        self.published = "Wed, 02 Oct 2002 13:00:00 GMT"
        self.enclosures = []
        self.author = "Test Author"
        self.authors = [{"name": "Test Author"}]

    def __getitem__(self, key):
        """Simulate dictionary access for mock entry."""
        print(f"Accessing key: {key}")  # Debug message
        if isinstance(key, int):
            return self.authors[key]  # Return author by index
        return getattr(self, key)

    def get(self, key, default=None):
        """Simulate dictionary 'get' method for mock entry."""
        return getattr(self, key, default)


@pytest.fixture
def create_user(client):
    """Fixture to create a test user."""
    response = client.post(
        "/register", data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code in (
        200,
        302,
    )  # Allow both 200 and 302 status codes


def test_no_site_url(client, auth, create_user):
    """Test case to handle missing site URL."""
    with client.application.app_context():
        # Log in with the test user
        auth.login()

        response = client.post("/add_feed", data={}, follow_redirects=True)
        assert response.status_code == 200
        assert b"No site URL provided." in response.data


def test_add_feed_success(client, auth, create_user, mocker):
    """Test case to successfully add a feed."""
    with client.application.app_context():
        # Log in with the test user
        auth.login()

        # Mock feedfinder2 and feedparser functions
        mocker.patch(
            "feedfinder2.find_feeds", return_value=["http://example.com/feed"]
        )
        mocker.patch("feedparser.parse", return_value=MockFeed())

        response = client.post(
            "/add_feed",
            data={
                "site_url": "http://example.com",
                "category": "Test Category",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Debug output
        print(response.json)

        assert response.json["success"] == True

        # Verify feed and feed item are added to the database
        feed = Feed.query.filter_by(url="http://example.com/feed").first()
        assert feed is not None
        assert feed.title == "Test Feed"

        feed_item = FeedItem.query.filter_by(
            link="http://example.com/entry"
        ).first()
        assert feed_item is not None
        assert feed_item.title == "Test Entry"


def test_feed_already_exists(client, auth, create_user, mocker):
    """Test case to handle already existing feed."""
    with client.application.app_context():
        # Log in with the test user
        auth.login()

        # Add an existing feed to the database
        existing_feed = Feed(
            url="http://example.com/feed", title="Existing Feed", user_id=1
        )
        db.session.add(existing_feed)
        db.session.commit()

        # Mock feedfinder2 and feedparser functions
        mocker.patch(
            "feedfinder2.find_feeds", return_value=["http://example.com/feed"]
        )
        mocker.patch("feedparser.parse", return_value=MockFeed())

        response = client.post(
            "/add_feed",
            data={
                "site_url": "http://example.com",
                "category": "Test Category",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert response.json["success"] == False
        assert response.json["error"] == "Feed already exists in the database"
