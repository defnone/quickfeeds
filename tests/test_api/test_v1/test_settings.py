import pytest
from flask import url_for
from app.models import User, Settings
from werkzeug.security import generate_password_hash
from app import db


@pytest.fixture
def create_user(app):
    """
    Fixture for creating a test user.
    """
    with app.app_context():
        password_hash = generate_password_hash("testpassword")
        user = User(username="testuser", password=password_hash)
        db.session.add(user)
        db.session.commit()
        return User.query.filter_by(username="testuser").first()


@pytest.fixture
def create_settings(app, create_user):
    """
    Fixture for creating user settings.
    """
    with app.app_context():
        settings = Settings(
            user_id=create_user.id,
            update_interval=30,
            timezone="UTC",
            language="English",
            unread=True,
            groq_api_key=None,
            translate=False,
        )
        db.session.add(settings)
        db.session.commit()
        return settings


def test_get_user_settings(client, auth, create_user, create_settings):
    """
    Test case for getting user settings.
    It checks if the response status code is 200 and if the returned settings
    match the expected values.
    """
    auth.login()
    with client.application.app_context():
        response = client.get(url_for("api_settings_blueprint.user_settings"))
        assert response.status_code == 200
        data = response.json
        assert data["update_interval"] == 30
        assert data["timezone"] == "UTC"
        assert data["language"] == "English"
        assert data["unread"] is True
        assert data["groq_api_key"] == None
        assert data["translate"] is False


def test_update_user_settings(client, auth, create_user, create_settings):
    """
    Test case for updating user settings.
    It checks if the response status code is 200 and if the returned settings
    match the updated values.
    """
    auth.login()
    with client.application.app_context():
        response = client.post(
            url_for("api_settings_blueprint.user_settings"),
            json={
                "update_interval": 60,
                "timezone": "PST",
                "language": "French",
                "unread": False,
                "groq_api_key": "new_api_key",
                "translate": True,
            },
        )
        assert response.status_code == 200
        data = response.json
        assert data["update_interval"] == 60
        assert data["timezone"] == "PST"
        assert data["language"] == "French"
        assert data["unread"] is False
        assert data["groq_api_key"] == "new_api_key"
        assert data["translate"] is True


def test_change_password(client, auth, create_user):
    """
    Test case for changing the user password.
    It checks if the response status code is 200 and if the password has been
    successfully changed.
    """
    auth.login()
    response = client.post(
        url_for("api_settings_blueprint.change_password"),
        json={
            "new_password": "newpassword",
            "confirm_password": "newpassword",
        },
    )
    assert response.status_code == 200
    assert response.json["status"] == "success"

    with client.application.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user is not None
        assert user.check_password("newpassword")


def test_update_user_settings_invalid_data(
    client, auth, create_user, create_settings
):
    """
    Test case for updating user settings with invalid data.
    It checks if the response status code is 400 and if the error message is
    correct.
    """
    auth.login()
    with client.application.app_context():
        response = client.post(
            url_for("api_settings_blueprint.user_settings"),
            json={
                "update_interval": 60,
                "timezone": "PST",
                "language": "French",
                "unread": "invalid",
                "groq_api_key": "new_api_key",
                "translate": False,
            },
        )
        assert response.status_code == 400
        assert "Not a boolean value" in response.json["error"]


def test_change_password_same_as_old(client, auth, create_user):
    """
    Test case for changing the password to the same as the old one.
    It checks if the response status code is 400 and if the error message is correct.
    """
    auth.login()
    with client.application.app_context():
        response = client.post(
            url_for("api_settings_blueprint.change_password"),
            json={
                "new_password": "testpassword",
                "confirm_password": "testpassword",
            },
        )
        assert response.status_code == 400
        assert (
            "New password must be different from the old password"
            in response.json["error"]
        )


def test_change_password_unauthenticated(client):
    """
    Test case for changing the password while unauthenticated.
    It checks if the response status code is 401 and if the error message is correct.
    """
    response = client.post(
        url_for("api_settings_blueprint.change_password"),
        json={
            "new_password": "newpassword",
            "confirm_password": "newpassword",
        },
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert response.json["error"] == "User not authenticated"
