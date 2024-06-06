import pytest
from flask import url_for
from app.models import Category, Feed, FeedItem
from werkzeug.security import generate_password_hash
from app import db


class MockFeed:
    def __init__(self):
        self.feed = {"title": "Test Feed"}
        self.entries = [MockEntry()]


class MockEntry:
    def __init__(self):
        self.title = "Test Entry"
        self.link = "http://example.com/entry"
        self.summary = "Test summary"
        self.published = "Wed, 02 Oct 2002 13:00:00 GMT"
        self.enclosures = []
        self.author = "Test Author"
        self.authors = [{"name": "Test Author"}]

    def __getitem__(self, key):
        print(f"Accessing key: {key}")  # Отладочное сообщение
        if isinstance(key, int):
            return self.authors[key]  # Возвращаем автора по индексу
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)


@pytest.fixture
def create_user(client):
    """Фикстура для создания тестового пользователя"""
    response = client.post(
        "/register", data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code in (
        200,
        302,
    )  # Разрешаем как 200, так и 302 статус


def test_no_site_url(client, auth, create_user):
    with client.application.app_context():
        # Логинимся под тестовым пользователем
        auth.login()

        response = client.post("/add_feed", data={}, follow_redirects=True)
        assert response.status_code == 200
        assert b"No site URL provided." in response.data


def test_add_feed_success(client, auth, create_user, mocker):
    with client.application.app_context():
        # Логинимся под тестовым пользователем
        auth.login()

        # Мокаем функции feedfinder2 и feedparser
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

        # Добавим вывод для отладки
        print(response.json)

        assert response.json["success"] == True

        # Проверяем, что фид и элемент фида добавлены в базу данных
        feed = Feed.query.filter_by(url="http://example.com/feed").first()
        assert feed is not None
        assert feed.title == "Test Feed"

        feed_item = FeedItem.query.filter_by(
            link="http://example.com/entry"
        ).first()
        assert feed_item is not None
        assert feed_item.title == "Test Entry"


def test_feed_already_exists(client, auth, create_user, mocker):
    with client.application.app_context():
        # Логинимся под тестовым пользователем
        auth.login()

        # Добавляем фид в базу данных
        existing_feed = Feed(
            url="http://example.com/feed", title="Existing Feed", user_id=1
        )
        db.session.add(existing_feed)
        db.session.commit()

        # Мокаем функции feedfinder2 и feedparser
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
