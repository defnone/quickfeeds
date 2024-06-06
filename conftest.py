from datetime import datetime
import pytest
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Settings, Category, Feed


@pytest.fixture
def app():
    print("Setting up the app fixture")
    app = create_app(config_name="testing")
    app.config.update(
        SERVER_NAME="localhost.localdomain", APPLICATION_ROOT="/"
    )
    with app.app_context():
        db.create_all()
        db.session.expire_on_commit = False
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    print("Setting up the client fixture")
    return app.test_client()


@pytest.fixture
def runner(app):
    print("Setting up the runner fixture")
    return app.test_cli_runner()


@pytest.fixture
def auth(client, create_user):
    return AuthActions(client, create_user)


class AuthActions:
    def __init__(self, client, user):
        self._client = client
        self.user = user

    def login(self, username="testuser", password="testpassword"):
        print(f"Logging in as {username}")
        response = self._client.post(
            "/login", data={"login": username, "password": password}
        )
        print(f"Login response status: {response.status_code}")
        return response

    def logout(self):
        print("Logging out")
        return self._client.get("/logout")


@pytest.fixture
def create_user(app):
    """
    Fixture for creating a test user.
    """
    with app.app_context():
        print("Creating a test user")
        password_hash = generate_password_hash("testpassword")
        user = User(
            username="testuser",
            password=password_hash,
            last_sync=datetime.now(),
        )
        db.session.add(user)
        db.session.commit()
        return User.query.filter_by(username="testuser").first()


@pytest.fixture
def create_settings(app, create_user):
    with app.app_context():
        settings = Settings(
            user_id=create_user.id,
            update_interval=30,
            timezone="UTC",
            language="en",
            unread=True,
            groq_api_key="dummy_api_key",
            translate=False,
        )
        db.session.add(settings)
        db.session.commit()
        return settings


@pytest.fixture
def create_category(app, create_user):
    """
    Fixture for creating a test category.
    """
    with app.app_context():
        category = Category(name="Test Category", user_id=create_user.id)
        db.session.add(category)
        db.session.commit()
        return category


@pytest.fixture
def create_feed(app, create_category):
    """
    Fixture for creating a test feed.
    """
    with app.app_context():
        feed = Feed(title="Test Feed", category_id=create_category.id)
        db.session.add(feed)
        db.session.commit()
        return feed


@pytest.fixture(autouse=True)
def check_test_config(app):
    """Fixture to check that the app is in testing mode"""
    print("Checking if the app is in testing mode")
    assert app.config["TESTING"] is True, "App is not running in testing mode"
