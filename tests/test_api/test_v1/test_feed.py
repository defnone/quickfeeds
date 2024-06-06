import pytest
from app.models import Feed
from flask import url_for
from app import db


@pytest.fixture
def create_feed(app, create_user):
    """
    Fixture for creating a test feed.
    """
    with app.app_context():
        feed = Feed(
            title="Test Feed", url="http://example.com", user_id=create_user.id
        )
        db.session.add(feed)
        db.session.commit()
        db.session.refresh(
            feed
        )  # Ensure the instance is attached to the session
        return feed


def test_update_feed(client, auth, create_feed):
    """
    Test updating a feed.
    """
    auth.login()
    response = client.put(
        url_for("api_feeds_blueprint.update_feed", feed_id=create_feed.id),
        json={"title": "Updated Test Feed"},
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert json_data["feed"]["title"] == "Updated Test Feed"


def test_update_feed_missing_title(client, auth, create_feed):
    """
    Test updating a feed with missing title.
    """
    auth.login()
    response = client.put(
        url_for("api_feeds_blueprint.update_feed", feed_id=create_feed.id),
        json={},
    )
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["error"] == "Title is required"


def test_delete_feed(client, auth, create_feed):
    """
    Test deleting a feed.
    """
    auth.login()
    response = client.delete(
        url_for("api_feeds_blueprint.delete_feed", feed_id=create_feed.id)
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    # Use Session.get() instead of Query.get()
    assert db.session.get(Feed, create_feed.id) is None


def test_update_feed_category(client, auth, create_feed):
    """
    Test updating a feed's category.
    """
    auth.login()
    response = client.put(
        url_for(
            "api_feeds_blueprint.update_feed_category", feed_id=create_feed.id
        ),
        json={"category_id": 2},
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert json_data["feed"]["category_id"] == 2


def test_update_feed_category_missing_category_id(client, auth, create_feed):
    """
    Test updating a feed's category with missing category ID.
    """
    auth.login()
    response = client.put(
        url_for(
            "api_feeds_blueprint.update_feed_category", feed_id=create_feed.id
        ),
        json={},
    )
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["error"] == "Category ID is required"


def test_update_feed_empty_title(client, auth, create_feed):
    """
    Test updating a feed with an empty title.
    """
    auth.login()
    response = client.put(
        url_for("api_feeds_blueprint.update_feed", feed_id=create_feed.id),
        json={"title": ""},
    )
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["error"] == "Title is required"


def test_update_feed_unauthorized(client, create_feed):
    """
    Test updating a feed without being logged in.
    """
    response = client.put(
        url_for("api_feeds_blueprint.update_feed", feed_id=create_feed.id),
        json={"title": "Updated Test Feed"},
    )
    assert response.status_code == 401
    json_data = response.get_json()
    assert json_data["error"] == "User not authenticated"


def test_delete_feed_unauthorized(client, create_feed):
    """
    Test deleting a feed without being logged in.
    """
    response = client.delete(
        url_for("api_feeds_blueprint.delete_feed", feed_id=create_feed.id)
    )
    assert response.status_code == 401
    json_data = response.get_json()
    assert json_data["error"] == "User not authenticated"


def test_update_feed_category_unauthorized(client, create_feed):
    """
    Test updating the category of a feed without being logged in.
    """
    response = client.put(
        url_for(
            "api_feeds_blueprint.update_feed_category", feed_id=create_feed.id
        ),
        json={"category_id": 2},
    )
    assert response.status_code == 401
    json_data = response.get_json()
    assert json_data["error"] == "User not authenticated"
