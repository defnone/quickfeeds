import pytest
from flask import url_for
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, Category


@pytest.fixture
def create_user(app):
    """
    Fixture to create a test user.
    """
    with app.app_context():
        password_hash = generate_password_hash("testpassword")
        user = User(username="testuser", password=password_hash)
        db.session.add(user)
        db.session.commit()
        return User.query.filter_by(username="testuser").first()


@pytest.fixture
def create_category(app, create_user):
    """
    Fixture to create a user's category.
    """
    with app.app_context():
        category = Category(name="Existing Category", user_id=create_user.id)
        db.session.add(category)
        db.session.commit()
        return category.id


def test_add_category(client, auth, create_user):
    """
    Test to add a new category.
    Checks that the response status code is 201 and the category is added correctly.
    """
    auth.login()
    response = client.post(
        url_for("settings_categories.add_category"),
        json={"name": "New Category"},
    )
    assert response.status_code == 201
    assert response.json["name"] == "New Category"


def test_add_category_unauthenticated(client):
    """
    Test to add a category without authentication.
    Checks that the response status code is 401 and an error message is returned.
    """
    response = client.post(
        url_for("settings_categories.add_category"),
        json={"name": "New Category"},
    )
    assert response.status_code == 401
    assert response.json["error"] == "User not authenticated"


def test_add_category_missing_name(client, auth, create_user):
    """
    Test to add a category without a name.
    Checks that the response status code is 400 and an error message is returned.
    """
    auth.login()
    response = client.post(
        url_for("settings_categories.add_category"), json={}
    )
    assert response.status_code == 400
    assert response.json["error"] == "Category name is required"


def test_add_category_duplicate_name(
    client, auth, create_user, create_category
):
    """
    Test to add a category with a duplicate name.
    Checks that the response status code is 400 and an error message is returned.
    """
    auth.login()
    response = client.post(
        url_for("settings_categories.add_category"),
        json={"name": "Existing Category"},
    )
    assert response.status_code == 400
    assert response.json["error"] == "Category already exists"


def test_delete_category(client, auth, create_user, create_category):
    """
    Test to delete a category.
    Checks that the response status code is 200 and the category is deleted successfully.
    """
    auth.login()
    response = client.delete(
        url_for(
            "settings_categories.delete_category", category_id=create_category
        )
    )
    assert response.status_code == 200
    assert response.json["message"] == "Category deleted"


def test_delete_category_unauthenticated(client):
    """
    Test to delete a category without authentication.
    Checks that the response status code is 401 and an error message is returned.
    """
    response = client.delete(
        url_for("settings_categories.delete_category", category_id=1)
    )
    assert response.status_code == 401
    assert response.json["error"] == "User not authenticated"


def test_delete_category_not_found(client, auth, create_user):
    """
    Test to delete a non-existent category.
    Checks that the response status code is 404 and an error message is returned.
    """
    auth.login()
    response = client.delete(
        url_for("settings_categories.delete_category", category_id=999)
    )
    assert response.status_code == 404
    assert response.json["error"] == "Category not found"


def test_rename_category(client, auth, create_user, create_category):
    """
    Test to rename a category.
    Checks that the response status code is 200 and the category is renamed successfully.
    """
    auth.login()
    response = client.post(
        url_for(
            "settings_categories.rename_category", category_id=create_category
        ),
        json={"new_name": "Renamed Category"},
    )
    assert response.status_code == 200
    assert response.json["message"] == "Category renamed"

    category = db.session.get(Category, create_category)
    assert category.name == "Renamed Category"


def test_rename_category_no_new_name(
    client, auth, create_user, create_category
):
    """
    Test to rename a category without specifying a new name.
    Checks that the response status code is 400 and an error message is returned.
    """
    auth.login()
    response = client.post(
        url_for(
            "settings_categories.rename_category", category_id=create_category
        ),
        json={},
    )
    assert response.status_code == 400
    assert response.json["error"] == "New name not provided"


def test_rename_category_not_found(client, auth, create_user):
    """
    Test to rename a non-existent category.
    Checks that the response status code is 404 and an error message is returned.
    """
    auth.login()
    response = client.post(
        url_for("settings_categories.rename_category", category_id=999),
        json={"new_name": "New Name"},
    )
    assert response.status_code == 404
    assert response.json["error"] == "Category not found"
