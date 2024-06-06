from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from app.models import Settings
from app.utils.groq import check_groq_api

api_groq_blueprint = Blueprint("api_groq_blueprint", __name__)


@api_groq_blueprint.route("/check", methods=["POST"])
@login_required
def check_groq():
    """
    Check the GROQ API for authentication and availability.

    Returns:
        A JSON response indicating the status of the GROQ API check.
        If the user is not authenticated, it returns an error message.
        If no GROQ API key is found for the user, it returns an error message.
        If the GROQ API check fails, it returns an error message.
        If the GROQ API check is successful, it returns a success message.
    """
    if not current_user.is_authenticated:
        return jsonify(
            {"status": "error", "message": "User not authenticated"}
        )

    user_settings = Settings.query.filter_by(user_id=current_user.id).first()

    if not user_settings or not user_settings.groq_api_key:
        return jsonify({"status": "error", "message": "No GROQ API key found"})

    if not check_groq_api("ping", user_settings.groq_api_key):
        return jsonify({"status": "error", "message": "GROQ API check failed"})

    return jsonify({"status": "success"})
