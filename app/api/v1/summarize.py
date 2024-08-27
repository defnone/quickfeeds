import logging
from flask import Blueprint, jsonify, request
from flask_login import current_user
from app.models import Settings
from app.utils.groq import groq_request
from app.utils.promts import SUMMARIZE
from app.utils.text import get_text_from_url, text_to_html_list
from app.utils.translate import translate_text_google

api_summarize_blueprint = Blueprint("api_summarize_blueprint", __name__)


@api_summarize_blueprint.route("", methods=["POST", "GET"])
def summarize():
    """
    This function handles the summarization of text from a given URL.
    It first checks if the user is authenticated and has a valid API key.
    If the user has requested translation, it translates the summarized text.
    The summarized (and possibly translated) text is then returned as a JSON
    response.
    """
    if not current_user.is_authenticated:
        return (
            jsonify({"status": "error", "error": "User not authenticated"}),
            401,
        )

    current_user_settings = Settings.query.filter_by(
        user_id=current_user.id
    ).first()

    if not current_user_settings.groq_api_key:
        return jsonify({"status": "error", "error": "Missing API key"}), 403

    data = request.get_json()
    if not data or not data.get("url"):
        return (
            jsonify(
                {"status": "error", "error": "Missing URL in request data"}
            ),
            400,
        )

    url = data.get("url")
    try:
        query = get_text_from_url(url, processor="goose3")
    except Exception as e:
        return (
            jsonify(
                {"status": "error", "error": f"Failed to get text: {str(e)}"}
            ),
            500,
        )
    if not query:
        return (
            jsonify(
                {"status": "error", "error": "Failed to get text from URL"}
            ),
            400,
        )

    try:
        response = groq_request(
            query, current_user_settings.groq_api_key, SUMMARIZE
        )
    except Exception as e:
        return (
            jsonify(
                {"status": "error", "error": f"Failed to summarize: {str(e)}"}
            ),
            500,
        )

    if current_user_settings.translate:
        try:
            response = translate_text_google(
                response, current_user_settings.language
            )
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": f"Failed to translate: {str(e)}",
                    }
                ),
                500,
            )

    response = text_to_html_list(response)
    print(response)
    if len(response) == 0:
        return (
            logging.error("Blank summary %s", response),
            jsonify(
                {
                    "status": "error",
                    "error": "Failed to summarize: blank response",
                }
            ),
            500,
        )

    return jsonify({"summary": response}), 200
