import pytest
from flask import url_for
from app import db
from app.models import Category, Feed, FeedItem, User
from datetime import datetime


def test_get_categories_and_blogs(client, auth, create_user):
    # Login the test user
    auth.login()

    # Create test data
    with client.application.app_context():
        category = Category(name="Test Category")
        db.session.add(category)
        db.session.commit()

        feed = Feed(
            category_id=category.id,
            user_id=create_user.id,
            title="Test Feed",
            url="http://example.com",
        )
        db.session.add(feed)
        db.session.commit()

        feed_item = FeedItem(
            feed_id=feed.id,
            title="Test Item",
            link="http://example.com/item",
            summary="Summary",
            pub_date=datetime.now(),
            creator="Creator",
            read=False,
            guid="test-guid",
        )
        db.session.add(feed_item)
        db.session.commit()

    response = client.get(url_for("api.get_categories_and_blogs"))
    data = response.get_json()

    assert response.status_code == 200
    assert len(data["categories_and_blogs"]) == 1
    assert data["categories_and_blogs"][0]["name"] == "Test Category"
    assert len(data["categories_and_blogs"][0]["feeds"]) == 1
    assert (
        data["categories_and_blogs"][0]["feeds"][0]["feed"]["title"]
        == "Test Feed"
    )
    assert data["categories_and_blogs"][0]["feeds"][0]["unread_count"] == 1


def test_get_last_sync(client, auth, create_user):
    # Login the test user
    auth.login()

    # Check the last_sync value
    with client.application.app_context():
        user = User.query.filter_by(id=create_user.id).first()
        print(f"last_sync: {user.last_sync}")  # Debugging output
        assert (
            user.last_sync is not None
        ), "last_sync should not be None after setting it"

    response = client.get(url_for("api.get_last_sync"))
    data = response.get_json()
    print(f"Response JSON: {data}")  # Debugging output

    assert response.status_code == 200
    assert "last_sync" in data
    assert data["last_sync"] != "Never"


def test_unread_count(client, auth, create_user):
    # Login the test user
    auth.login()

    # Create test data
    with client.application.app_context():
        feed = Feed(
            user_id=create_user.id, title="Test Feed", url="http://example.com"
        )
        db.session.add(feed)
        db.session.commit()

        feed_item = FeedItem(
            feed_id=feed.id,
            title="Test Item",
            link="http://example.com/item",
            summary="Summary",
            pub_date=datetime.now(),
            creator="Creator",
            read=False,
            guid="test-guid",
        )
        db.session.add(feed_item)
        db.session.commit()

    response = client.get(url_for("api.unread_count"))
    data = response.get_json()

    assert response.status_code == 200
    assert data["unread_count"] == 1
