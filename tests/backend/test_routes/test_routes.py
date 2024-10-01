"""
Unit tests for the Flask routes in the application.

These tests ensure that the various routes in the application behave as expected
under different conditions. The routes tested include index, category, feed, and settings.

Fixtures:
    app: Initializes the Flask application in testing mode.
    client: Provides a test client for the Flask application.
    init_db: Sets up and tears down the database for each test.
    login_user: Logs in a test user by creating a user record in the database and
                setting the session to simulate a logged-in state.

Tests:
    test_index_route_no_unread:
        Verifies that the index route redirects to the 'all_items' route when there are no unread items.

    test_index_route_with_unread:
        Verifies that the index route renders the index page correctly when there are unread items.

    test_category_route_no_unread:
        Verifies that the category route redirects to the 'all_category_items' route when there are no unread items in the specified category.

    test_category_route_with_unread:
        Verifies that the category route renders the category items page correctly when there are unread items in the specified category.

    test_feed_route_no_unread:
        Verifies that the feed route redirects to the 'all_feed_items' route when there are no unread items in the specified feed.

    test_feed_route_with_unread:
        Verifies that the feed route renders the feed items page correctly when there are unread items in the specified feed.

    test_settings_route:
        Verifies that the settings route renders the settings page correctly and contains the list of timezones.

    test_category_not_found:
        Verifies that the category route handles the case when the specified category is not found.

    test_feed_not_found:
        Verifies that the feed route handles the case when the specified feed is not found.

    test_all_category_items_route:
        Verifies that the 'all_category_items' route renders the correct page when there are no unread items in the category.

    test_all_feed_items_route:
        Verifies that the 'all_feed_items' route renders the correct page when there are no unread items in the feed.

    test_settings_post_route:
        Verifies that the settings route correctly handles POST requests.
"""

import pytest
from flask import url_for
from app import create_app, db
from app.models import Category, Feed, Settings, User


@pytest.fixture
def app():
    app = create_app("testing")
    app.config.update(
        {
            "SERVER_NAME": "localhost",
            "PREFERRED_URL_SCHEME": "http",
        }
    )
    app_context = app.app_context()
    app_context.push()

    yield app

    app_context.pop()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def init_db(app):
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()


@pytest.fixture
def login_user(client, init_db):
    user = User(id=1, username="testuser", password="testpassword")
    db.session.add(user)
    db.session.commit()
    with client.session_transaction() as session:
        session["_user_id"] = "1"
    return client


def test_index_route_no_unread(init_db, login_user):
    user_settings = Settings(user_id=1, unread=False)
    db.session.add(user_settings)
    db.session.commit()

    response = login_user.get(url_for("routes.index"))
    assert response.status_code == 302
    assert response.headers["Location"] == url_for(
        "routes.all_items", _external=False
    )


def test_index_route_with_unread(init_db, login_user):
    user_settings = Settings(user_id=1, unread=True)
    db.session.add(user_settings)
    db.session.commit()

    response = login_user.get(url_for("routes.index"))
    assert response.status_code == 200
    assert b"All Unread feeds" in response.data


def test_category_route_no_unread(init_db, login_user):
    user_settings = Settings(user_id=1, unread=False)
    category = Category(id=1, name="Tech")
    db.session.add(user_settings)
    db.session.add(category)
    db.session.commit()

    response = login_user.get(url_for("routes.category_items", cat_id=1))
    assert response.status_code == 302
    assert response.headers["Location"] == url_for(
        "routes.all_category_items", cat_id=1, _external=False
    )


def test_category_route_with_unread(init_db, login_user):
    user_settings = Settings(user_id=1, unread=True)
    category = Category(id=1, name="Tech")
    db.session.add(user_settings)
    db.session.add(category)
    db.session.commit()

    response = login_user.get(url_for("routes.category_items", cat_id=1))
    assert response.status_code == 200
    assert b"Unread Tech category" in response.data


def test_feed_route_no_unread(init_db, login_user):
    user_settings = Settings(user_id=1, unread=False)
    category = Category(id=1, name="Tech")
    feed = Feed(
        id=1,
        title="Python News",
        url="http://example.com",
        user_id=1,
        category_id=1,
    )
    db.session.add(user_settings)
    db.session.add(category)
    db.session.add(feed)
    db.session.commit()

    response = login_user.get(
        url_for("routes.feed_items", cat_id=1, feed_id=1)
    )
    assert response.status_code == 302
    assert response.headers["Location"] == url_for(
        "routes.all_feed_items", cat_id=1, feed_id=1, _external=False
    )


def test_feed_route_with_unread(init_db, login_user):
    user_settings = Settings(user_id=1, unread=True)
    category = Category(id=1, name="Tech")
    feed = Feed(
        id=1,
        title="Python News",
        url="http://example.com",
        user_id=1,
        category_id=1,
    )
    db.session.add(user_settings)
    db.session.add(category)
    db.session.add(feed)
    db.session.commit()

    response = login_user.get(
        url_for("routes.feed_items", cat_id=1, feed_id=1)
    )
    assert response.status_code == 200
    assert b"Unread Python News" in response.data


def test_settings_route(init_db, login_user):
    response = login_user.get(url_for("routes.settings"))
    assert response.status_code == 200
    assert b"Settings" in response.data
    assert b"GMT" in response.data  # Checking for a common timezone name


def test_category_not_found(init_db, login_user):
    user_settings = Settings(user_id=1, unread=True)
    db.session.add(user_settings)
    db.session.commit()

    response = login_user.get(url_for("routes.category_items", cat_id=999))
    assert response.status_code == 302
    assert response.headers["Location"] == url_for(
        "routes.index", _external=False
    )


def test_feed_not_found(init_db, login_user):
    user_settings = Settings(user_id=1, unread=True)
    db.session.add(user_settings)
    db.session.commit()

    response = login_user.get(
        url_for("routes.feed_items", cat_id=1, feed_id=999)
    )
    assert response.status_code == 302
    assert response.headers["Location"] == url_for(
        "routes.index", _external=False
    )


def test_all_category_items_route(init_db, login_user):
    user_settings = Settings(user_id=1, unread=False)
    category = Category(id=1, name="Tech")
    db.session.add(user_settings)
    db.session.add(category)
    db.session.commit()

    response = login_user.get(url_for("routes.all_category_items", cat_id=1))
    assert response.status_code == 200
    assert b"All Tech category" in response.data


def test_all_feed_items_route(init_db, login_user):
    user_settings = Settings(user_id=1, unread=False)
    category = Category(id=1, name="Tech")
    feed = Feed(
        id=1,
        title="Python News",
        url="http://example.com",
        user_id=1,
        category_id=1,
    )
    db.session.add(user_settings)
    db.session.add(category)
    db.session.add(feed)
    db.session.commit()

    response = login_user.get(
        url_for("routes.all_feed_items", cat_id=1, feed_id=1)
    )
    assert response.status_code == 200
    assert b"All Python News" in response.data


def test_settings_post_route(init_db, login_user):
    data = {"timezone": "UTC"}
    response = login_user.post(url_for("routes.settings"), data=data)
    assert response.status_code == 200
    assert b"Settings" in response.data
    assert b"UTC" in response.data
