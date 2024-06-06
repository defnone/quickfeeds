import pytest
from flask import json
from app import create_app, db
from app.models import User, Settings
from unittest.mock import patch
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """
    Fixture to create a Flask application for testing.
    It sets up the application context, creates all database tables,
    and tears them down after the test is done.
    """
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """
    Fixture to provide a test client for the Flask application.
    """
    return app.test_client()


@pytest.fixture
def auth(client):
    """
    Fixture to handle authentication actions like login and logout.
    """

    class AuthActions:
        def __init__(self, client):
            self._client = client

        def login(self, username="testuser", password="testpassword"):
            return self._client.post(
                "/login", data={"login": username, "password": password}
            )

        def logout(self):
            return self._client.get("/logout")

    return AuthActions(client)


@pytest.fixture
def create_user(app):
    """
    Fixture to create a test user in the database.
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
    Fixture to create settings for the test user in the database.
    """
    with app.app_context():
        settings = Settings(
            user_id=create_user.id,
            update_interval=30,
            timezone="UTC",
            language="English",
            unread=True,
            groq_api_key="fake_key",
            translate=False,
        )
        db.session.add(settings)
        db.session.commit()
        return settings


@patch("app.api.v1.summarize.groq_request")
def test_api_summarize_authenticated(
    mock_groq_request, client, auth, create_user, create_settings
):
    """
    Test the API summarization endpoint when the user is authenticated.
    """
    auth.login(username="testuser", password="testpassword")

    mock_groq_request.return_value = "Summarized text"
    response = client.post(
        "/api/summarize/",
        json={"url": "http://example.com"},
        content_type="application/json",
    )
    assert response.status_code == 200

    data = response.get_json()
    assert "summary" in data


def test_user_not_authenticated(client):
    """
    Test the API summarization endpoint when the user is not authenticated.
    """
    response = client.post("/api/summarize/", content_type="application/json")
    assert response.status_code == 401
    assert "User not authenticated" in response.json["error"]


@patch("app.api.v1.summarize.groq_request")
def test_missing_api_key(
    mock_groq_request, client, auth, create_user, create_settings
):
    """
    Test the API summarization endpoint when the API key is missing.
    """
    auth.login(username="testuser", password="testpassword")

    with client.application.app_context():
        # Update user settings within the application context
        settings = Settings.query.filter_by(user_id=create_user.id).first()
        settings.groq_api_key = None
        db.session.commit()

    response = client.post(
        "/api/summarize/",
        json={"url": "http://example.com"},
        content_type="application/json",
    )
    assert response.status_code == 403
    assert "Missing API key" in response.json["error"]


@patch("app.api.v1.summarize.groq_request")
def test_missing_url_in_request_data(
    mock_groq_request, client, auth, create_user, create_settings
):
    """
    Test the API summarization endpoint when the URL is missing in request data.
    """
    auth.login(username="testuser", password="testpassword")

    response = client.post(
        "/api/summarize/", json={}, content_type="application/json"
    )
    assert response.status_code == 400
    assert "Missing URL in request data" in response.json["error"]


@patch("app.api.v1.summarize.get_text_from_url")
@patch("app.api.v1.summarize.groq_request")
def test_failed_to_get_text_from_url(
    mock_groq_request,
    mock_get_text,
    client,
    auth,
    create_user,
    create_settings,
):
    """
    Test the API summarization endpoint when it fails to get text from the provided URL.
    """
    auth.login(username="testuser", password="testpassword")

    mock_get_text.return_value = None
    response = client.post(
        "/api/summarize/",
        json={"url": "http://example.com"},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Failed to get text from URL" in response.json["error"]


@patch("app.api.v1.summarize.text_to_html_list")
@patch("app.api.v1.summarize.groq_request")
@patch("app.api.v1.summarize.get_text_from_url")
def test_successful_summarization(
    mock_get_text,
    mock_groq_request,
    mock_text_to_html_list,
    client,
    auth,
    create_user,
    create_settings,
):
    """
    Test the API summarization endpoint for a successful summarization.
    """
    auth.login(username="testuser", password="testpassword")

    mock_get_text.return_value = "Sample text"
    mock_groq_request.return_value = "Summarized text"
    mock_text_to_html_list.return_value = ["Summarized text"]
    response = client.post(
        "/api/summarize/",
        json={"url": "http://example.com"},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert "Summarized text" in response.json["summary"]


@patch("app.api.v1.summarize.text_to_html_list")
@patch("app.api.v1.summarize.translate_text_google")
@patch("app.api.v1.summarize.groq_request")
def test_translation(
    mock_groq_request,
    mock_translate,
    mock_text_to_html_list,
    client,
    auth,
    create_user,
    create_settings,
):
    """
    Test the API summarization endpoint for a successful translation.
    """
    auth.login(username="testuser", password="testpassword")

    with client.application.app_context():
        # Update user settings within the application context
        settings = Settings.query.filter_by(user_id=create_user.id).first()
        settings.translate = True
        db.session.commit()

    mock_translate.return_value = "Translated text"
    mock_groq_request.return_value = "Summarized text"
    mock_text_to_html_list.return_value = ["Translated text"]
    response = client.post(
        "/api/summarize/",
        json={"url": "http://example.com", "translate": True},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert "Translated text" in response.json["summary"]
