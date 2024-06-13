from flask import Blueprint, jsonify, request
from flask_login import current_user
from app import db
from app.models import Category

settings_categories_blueprint = Blueprint("settings_categories", __name__)


@settings_categories_blueprint.route("/add", methods=["POST"])
def add_category():
    """
    Add a new category to the user's settings.

    Returns:
        A JSON response containing the newly created category if successful,
        or an error message if there was an issue with the request.

    Status Codes:
        201 Created: The category was successfully created.
        400 Bad Request: The request could not be understood or was missing
        required parameters.
        401 Unauthorized: Authentication failed or was not provided.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401

    data = request.get_json()
    category_name = data.get("name")

    if not category_name:
        return jsonify({"error": "Category name is required"}), 400

    existing_category = Category.query.filter_by(
        name=category_name, user_id=current_user.id
    ).first()
    if existing_category:
        return jsonify({"error": "Category already exists"}), 400

    new_category = Category(name=category_name, user_id=current_user.id)
    db.session.add(new_category)
    db.session.commit()

    return jsonify(new_category.to_dict()), 201


@settings_categories_blueprint.route(
    "/delete/<int:category_id>", methods=["DELETE"]
)
def delete_category(category_id):
    """
    Delete a category by its ID.

    Args:
        category_id (int): The ID of the category to be deleted.

    Returns:
        A JSON response containing a message indicating the success or failure of the deletion.

    Status Codes:
        200 OK: The category was successfully deleted.
        401 Unauthorized: If the user is not authenticated.
        404 Not Found: If the category with the specified ID is not found.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401

    category = db.session.get(Category, category_id)
    if not category:
        return jsonify({"error": "Category not found"}), 404

    if category.feeds:
        unnamed_category = Category.query.filter_by(
            name="Unnamed", user_id=current_user.id
        ).first()
        if not unnamed_category:
            unnamed_category = Category(
                name="Unnamed", user_id=current_user.id
            )
            db.session.add(unnamed_category)

        for feed in category.feeds:
            feed.category = unnamed_category

    db.session.delete(category)
    db.session.commit()

    return jsonify({"message": "Category deleted"}), 200


@settings_categories_blueprint.route(
    "/rename/<int:category_id>", methods=["POST"]
)
def rename_category(category_id):
    """
    Rename an existing category.

    Parameters:
        category_id (int): The ID of the category to rename.

    Returns:
        A JSON response containing a success message if the category was renamed successfully,
        or an error message if there was an issue with the request.

    Status Codes:
        200 OK: The category was successfully renamed.
        400 Bad Request: The request could not be understood or was missing required parameters.
        401 Unauthorized: Authentication failed or was not provided.
        404 Not Found: The requested category could not be found.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401

    category = db.session.get(Category, category_id)
    if not category:
        return jsonify({"error": "Category not found"}), 404

    new_name = request.json.get("new_name")
    if not new_name:
        return jsonify({"error": "New name not provided"}), 400

    category.name = new_name
    db.session.commit()

    return jsonify({"message": "Category renamed"}), 200
