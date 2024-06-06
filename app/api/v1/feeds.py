from flask import Blueprint, flash, jsonify, request
from flask_login import current_user
from app import db
from app.models import Feed
from sqlalchemy.exc import SQLAlchemyError

api_feeds_blueprint = Blueprint("api_feeds_blueprint", __name__)


@api_feeds_blueprint.route("/<int:feed_id>", methods=["PUT"])
def update_feed(feed_id):
    """
    Update the title of a feed.
    ---
    Parameters:
        feed_id (int): The ID of the feed to be updated.
    Request Body:
        title (str): The new title for the feed.
    Responses:
        200: Feed updated successfully.
        400: Title is required.
        401: User not authenticated.
        404: Feed not found.
        500: Database error occurred.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401

    data = request.get_json()
    title = data.get("title")

    if not title:
        return jsonify({"error": "Title is required"}), 400

    try:
        feed = db.session.get(Feed, feed_id)
        if not feed:
            return jsonify({"error": "Feed not found"}), 404

        feed.title = title
        db.session.commit()
        flash("Feed updated successfully", "success")
        return (
            jsonify(
                {
                    "status": "success",
                    "feed": {"id": feed.id, "title": feed.title},
                }
            ),
            200,
        )

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@api_feeds_blueprint.route("/<int:feed_id>", methods=["DELETE"])
def delete_feed(feed_id):
    """
    Delete a feed.
    ---
    Parameters:
        feed_id (int): The ID of the feed to be deleted.
    Responses:
        200: Feed deleted successfully.
        401: User not authenticated.
        404: Feed not found.
        500: Database error occurred.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401

    try:
        feed = db.session.get(Feed, feed_id)
        if not feed:
            return jsonify({"error": "Feed not found"}), 404

        db.session.delete(feed)
        db.session.commit()
        flash("Feed deleted successfully", "success")
        return jsonify({"status": "success"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@api_feeds_blueprint.route("/<int:feed_id>/category", methods=["PUT"])
def update_feed_category(feed_id):
    """
    Update the category of a feed.
    ---
    Parameters:
        feed_id (int): The ID of the feed to be updated.
    Request Body:
        category_id (int): The new category ID for the feed.
    Responses:
        200: Feed category updated successfully.
        400: Category ID is required.
        401: User not authenticated.
        404: Feed not found.
        500: Database error occurred.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401

    data = request.get_json()
    category_id = data.get("category_id")

    if not category_id:
        return jsonify({"error": "Category ID is required"}), 400

    try:
        feed = db.session.get(Feed, feed_id)
        if not feed:
            return jsonify({"error": "Feed not found"}), 404

        feed.category_id = category_id
        db.session.commit()
        flash("Feed category updated successfully", "success")
        return (
            jsonify(
                {
                    "status": "success",
                    "feed": {"id": feed.id, "category_id": feed.category_id},
                }
            ),
            200,
        )

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
