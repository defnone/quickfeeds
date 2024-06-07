from flask import Blueprint, jsonify, request
from flask_login import current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models import Settings

api_settings_blueprint = Blueprint("api_settings_blueprint", __name__)


@api_settings_blueprint.route("", methods=["GET", "POST"])
def user_settings():
    """
    Handle GET and POST requests for user settings.

    If the user is authenticated, this function will return the user's settings
    in a JSON format for a GET request, and update the user's settings for a
    POST request.

    If the user is not authenticated, this function will return an error
    message.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401

    # Fetch the current user's settings
    current_user_settings = Settings.query.filter_by(
        user_id=current_user.id
    ).first()

    if request.method == "GET":
        # If the user has a GROQ API key, replace it with asterisks for
        # security
        if current_user_settings.groq_api_key:
            current_user_settings.groq_api_key = (
                "******************************"
            )
        else:
            current_user_settings.groq_api_key = None
        # Return the user's settings in a JSON format
        return (
            jsonify(
                update_interval=current_user_settings.update_interval,
                timezone=current_user_settings.timezone,
                language=current_user_settings.language,
                unread=current_user_settings.unread,
                groq_api_key=current_user_settings.groq_api_key,
                translate=current_user_settings.translate,
            ),
            200,
        )

    if request.method == "POST":
        # Extract the data from the request
        update_data = request.json

        # Validate boolean fields
        if "unread" in update_data and not isinstance(
            update_data["unread"], bool
        ):
            return jsonify({"error": "Not a boolean value: 'unread'"}), 400
        if "translate" in update_data and not isinstance(
            update_data["translate"], bool
        ):
            return (
                jsonify({"error": "Not a boolean value: 'translate'"}),
                400,
            )

        if current_user_settings:
            # If the user has settings, update them
            for key, value in update_data.items():
                if hasattr(current_user_settings, key):
                    setattr(current_user_settings, key, value)
        else:
            # If the user doesn't have settings, create them with default
            # values
            default_values = {
                "update_interval": 60,
                "timezone": "UTC",
                "language": "English",
                "unread": True,
                "groq_api_key": None,
                "translate": False,
            }
            default_values.update(update_data)
            current_user_settings = Settings(
                user_id=current_user.id, **default_values
            )
        # Add the updated settings to the session and commit the changes
        db.session.add(current_user_settings)
        db.session.commit()

        # Return the updated settings in a JSON format
        return (
            jsonify(
                update_interval=current_user_settings.update_interval,
                timezone=current_user_settings.timezone,
                language=current_user_settings.language,
                unread=current_user_settings.unread,
                groq_api_key=current_user_settings.groq_api_key,
                translate=current_user_settings.translate,
            ),
            200,
        )


@api_settings_blueprint.route("/change_password", methods=["POST"])
def change_password():
    """
    Handle POST requests to change the current user's password.

    This function expects a JSON object in the request body with two fields:
    'new_password' and 'confirm_password'. If these fields are not provided or
    do not match, the function will return an error. If they match, the
    function will update the current user's password and return a success
    status.
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401

    # Extract the data from the request
    data = request.get_json()
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    # Check that both fields were provided
    if not new_password or not confirm_password:
        return jsonify({"error": "All fields are required"}), 400

    # Check that the passwords match
    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 422

    # Check that the new password is different from the old password
    if current_user.check_password(new_password):
        return (
            jsonify(
                {
                    "error": "New password must be different from the old password"
                }
            ),
            400,
        )

    # Generate a hash of the new password
    new_password = generate_password_hash(new_password)

    # Update the current user's password and commit the changes
    current_user.password = new_password
    db.session.add(current_user)
    db.session.commit()

    # Return a success status
    return jsonify({"status": "success"}), 200
