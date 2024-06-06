import pytest
from flask import url_for
from app.models import Feed, FeedItem
import pytz
from app import db
from datetime import datetime, timezone


def test_get_feed_items(client, auth, create_user, create_settings):
    """
    Test fetching unread feed items for the current user.
    """
    auth.login()
    response = client.get(url_for("api_feeditems_blueprint.get_feed_items"))
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_get_all_feed_items(client, auth, create_user, create_settings):
    """
    Test fetching all feed items for the current user.
    """
    auth.login()
    response = client.get(
        url_for("api_feeditems_blueprint.get_all_feed_items")
    )
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_get_category_feed_items(client, auth, create_user, create_settings):
    """
    Test fetching unread feed items for a specific category.
    """
    auth.login()
    category_id = 1
    response = client.get(
        url_for(
            "api_feeditems_blueprint.get_category_feed_items",
            cat_id=category_id,
        )
    )
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_get_all_category_feed_items(
    client, auth, create_user, create_settings
):
    """
    Test fetching all feed items for a specific category.
    """
    auth.login()
    category_id = 1
    response = client.get(
        url_for(
            "api_feeditems_blueprint.get_all_category_feed_items",
            cat_id=category_id,
        )
    )
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_get_specific_feed_items(client, auth, create_user, create_settings):
    """
    Test fetching unread feed items for a specific feed within a category.
    """
    auth.login()
    category_id = 1
    feed_id = 1
    response = client.get(
        url_for(
            "api_feeditems_blueprint.get_specific_feed_items",
            cat_id=category_id,
            feed_id=feed_id,
        )
    )
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_get_all_specific_feed_items(
    client, auth, create_user, create_settings
):
    """
    Test fetching all feed items for a specific feed within a category.
    """
    auth.login()
    category_id = 1
    feed_id = 1
    response = client.get(
        url_for(
            "api_feeditems_blueprint.get_all_specific_feed_items",
            cat_id=category_id,
            feed_id=feed_id,
        )
    )
    assert response.status_code == 200
    assert isinstance(response.json, list)


# Additional helper function to create feed items
@pytest.fixture
def create_feed_items(app, create_user, create_settings):
    """
    Fixture for creating feed items.
    """
    with app.app_context():
        feed = Feed(
            user_id=create_user.id,
            category_id=1,
            title="Test Feed",
            url="http://example.com",
        )
        db.session.add(feed)
        db.session.commit()
        feed_item = FeedItem(
            feed_id=feed.id,
            title="Test Feed Item",
            link="http://example.com",
            pub_date=datetime.now(timezone.utc),
            read=False,
        )
        db.session.add(feed_item)
        db.session.commit()
        return feed.id, feed_item.id


# Update tests to include the creation of feed items
def test_get_feed_items_with_data(
    client, auth, create_user, create_settings, create_feed_items
):
    """
    Test fetching unread feed items for the current user with data.
    """
    auth.login()
    response = client.get(url_for("api_feeditems_blueprint.get_feed_items"))
    assert response.status_code == 200
    assert len(response.json) > 0


def test_get_all_feed_items_with_data(
    client, auth, create_user, create_settings, create_feed_items
):
    """
    Test fetching all feed items for the current user with data.
    """
    auth.login()
    response = client.get(
        url_for("api_feeditems_blueprint.get_all_feed_items")
    )
    assert response.status_code == 200
    assert len(response.json) > 0


def test_get_category_feed_items_with_data(
    client, auth, create_user, create_settings, create_feed_items
):
    """
    Test fetching unread feed items for a specific category with data.
    """
    auth.login()
    category_id = 1
    response = client.get(
        url_for(
            "api_feeditems_blueprint.get_category_feed_items",
            cat_id=category_id,
        )
    )
    assert response.status_code == 200
    assert len(response.json) > 0


def test_get_all_category_feed_items_with_data(
    client, auth, create_user, create_settings, create_feed_items
):
    """
    Test fetching all feed items for a specific category with data.
    """
    auth.login()
    category_id = 1
    response = client.get(
        url_for(
            "api_feeditems_blueprint.get_all_category_feed_items",
            cat_id=category_id,
        )
    )
    assert response.status_code == 200
    assert len(response.json) > 0


def test_get_specific_feed_items_with_data(
    client, auth, create_user, create_settings, create_feed_items
):
    """
    Test fetching unread feed items for a specific feed within a category with data.
    """
    auth.login()
    category_id = 1
    feed_id, feed_item_id = create_feed_items
    response = client.get(
        url_for(
            "api_feeditems_blueprint.get_specific_feed_items",
            cat_id=category_id,
            feed_id=feed_id,
        )
    )
    assert response.status_code == 200
    assert len(response.json) > 0


def test_get_all_specific_feed_items_with_data(
    client, auth, create_user, create_settings, create_feed_items
):
    """
    Test fetching all feed items for a specific feed within a category with data.
    """
    auth.login()
    category_id = 1
    feed_id, feed_item_id = create_feed_items
    response = client.get(
        url_for(
            "api_feeditems_blueprint.get_all_specific_feed_items",
            cat_id=category_id,
            feed_id=feed_id,
        )
    )
    assert response.status_code == 200
    assert len(response.json) > 0
