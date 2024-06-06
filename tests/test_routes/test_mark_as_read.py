import pytest
from flask import url_for
from flask_login import login_user
from app import create_app, db
from app.models import User, Feed, FeedItem, Category
from flask_testing import TestCase
from werkzeug.security import generate_password_hash


class MarkAsReadTestCase(TestCase):
    def create_app(self):
        """
        Creates and configures the app for testing.

        Returns:
            Flask app instance configured for testing.
        """
        app = create_app("testing")  # or provide your testing configurations
        return app

    def setUp(self):
        """
        Sets up the test environment before each test.
        - Creates the database and necessary tables.
        - Creates a test user and logs in.
        - Creates a test category, feed, and feed item.
        """
        db.create_all()
        self.user = User(
            username="testuser", password=generate_password_hash("password")
        )
        db.session.add(self.user)
        db.session.commit()

        # Log in the test user
        login_user(self.user)

        # Create test data
        self.category = Category(name="Test Category", user_id=self.user.id)
        db.session.add(self.category)
        db.session.commit()

        self.feed = Feed(
            user_id=self.user.id,
            url="http://testfeed.com",
            category_id=self.category.id,
        )
        db.session.add(self.feed)
        db.session.commit()

        self.feed_item = FeedItem(
            feed_id=self.feed.id, title="Test Item", link="http://testitem.com"
        )
        db.session.add(self.feed_item)
        db.session.commit()

    def tearDown(self):
        """
        Tears down the test environment after each test.
        - Removes the database session.
        - Drops all tables from the database.
        """
        db.session.remove()
        db.drop_all()

    def test_mark_as_read(self):
        """
        Tests the mark_as_read endpoint.
        - Sends a POST request to mark a specific feed item as read.
        - Asserts that the response status is 200.
        - Asserts that the feed item is marked as read.
        """
        response = self.client.post(
            url_for("mark_as_read.mark_as_read", item_id=self.feed_item.id)
        )
        assert response.status_code == 200
        feed_item = db.session.get(FeedItem, self.feed_item.id)
        assert feed_item.read == True

    def test_mark_as_read_all(self):
        """
        Tests the mark_as_read_all endpoint.
        - Sends a POST request to mark all feed items as read for the current user.
        - Asserts that the response status is 302 (Redirect).
        - Asserts that all feed items are marked as read.
        """
        response = self.client.post(url_for("mark_as_read.mark_as_read_all"))
        assert response.status_code == 302  # Redirect status
        feed_items = FeedItem.query.all()
        for item in feed_items:
            assert item.read == True

    def test_mark_as_read_all_category(self):
        """
        Tests the mark_as_read_all_category endpoint.
        - Sends a POST request to mark all feed items in a category as read for the current user.
        - Asserts that the response status is 302 (Redirect).
        - Asserts that all feed items in the category are marked as read.
        """
        response = self.client.post(
            url_for(
                "mark_as_read.mark_as_read_all_category",
                cat_id=self.category.id,
            )
        )
        assert response.status_code == 302  # Redirect status
        feed_items = FeedItem.query.filter_by(feed_id=self.feed.id).all()
        for item in feed_items:
            assert item.read == True

    def test_mark_as_read_all_feed(self):
        """
        Tests the mark_as_read_all_feed endpoint.
        - Sends a POST request to mark all feed items in a specific feed as read for the current user.
        - Asserts that the response status is 302 (Redirect).
        - Asserts that all feed items in the specified feed are marked as read.
        """
        response = self.client.post(
            url_for(
                "mark_as_read.mark_as_read_all_feed",
                cat_id=self.category.id,
                feed_id=self.feed.id,
            )
        )
        assert response.status_code == 302  # Redirect status
        feed_items = FeedItem.query.filter_by(feed_id=self.feed.id).all()
        for item in feed_items:
            assert item.read == True


if __name__ == "__main__":
    pytest.main()
