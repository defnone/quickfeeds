import pytest
from flask import url_for
from werkzeug.security import generate_password_hash
from app.models import User, Settings
from app import db
import warnings


@pytest.fixture
def new_user(app):
    with app.app_context():
        user = User(
            username="testuser",
            password=generate_password_hash("testpassword"),
        )
        db.session.add(user)
        db.session.commit()
        settings = Settings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()
        return User.query.filter_by(
            username="testuser"
        ).first()  # Возвращаем пользователя из сессии


@pytest.fixture
def init_database(app):
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


def test_register(client, init_database):
    with client.application.app_context():
        response = client.post(
            url_for("auth.register"),
            data={"username": "newuser", "password": "newpassword"},
        )
        assert response.status_code == 302, response.data
        user = User.query.filter_by(username="newuser").first()
        assert user is not None


def test_login(client, init_database, new_user):
    with client.application.app_context():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            response = client.post(
                url_for("auth.login"),
                data={"login": new_user.username, "password": "testpassword"},
                follow_redirects=True,
            )
        assert response.status_code == 200
        assert b"You have logged in" in response.data


def test_logout(client, init_database, new_user):
    with client.application.app_context():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            response = client.post(
                url_for("auth.login"),
                data={"login": new_user.username, "password": "testpassword"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            response = client.get(
                url_for("auth.logout"), follow_redirects=True
            )
        assert response.status_code == 200
        assert b"You have logged out" in response.data
