from datetime import datetime, timedelta, UTC
import logging
import pytz
from flask import Blueprint, jsonify, request
from flask_login import current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models import Settings, User, Feed

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

        # If the user has an OpenAI API key, replace it with asterisks for
        # security
        if current_user_settings.openai_api_key:
            current_user_settings.openai_api_key = (
                "******************************"
            )
        else:
            current_user_settings.openai_api_key = None

        # Return the user's settings in a JSON format
        return (
            jsonify(
                update_interval=current_user_settings.update_interval,
                timezone=current_user_settings.timezone,
                language=current_user_settings.language,
                unread=current_user_settings.unread,
                groq_api_key=current_user_settings.groq_api_key,
                translate=current_user_settings.translate,
                clean_after_days=current_user_settings.clean_after_days,
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

        # Validate integer fields and set default value for clean_after_days
        if "clean_after_days" in update_data:
            clean_after_days = int(update_data["clean_after_days"])
            if not isinstance(clean_after_days, int) or clean_after_days < 1:
                return (
                    jsonify({"error": "Not a valid value.'"}),
                    400,
                )

        # If the user has settings, update them
        if current_user_settings:
            for key, value in update_data.items():
                if hasattr(current_user_settings, key):
                    setattr(current_user_settings, key, value)
        else:
            # If the user doesn't have settings,
            # create them with default values
            default_values = {
                "update_interval": 60,
                "timezone": "UTC",
                "language": "English",
                "unread": True,
                "groq_api_key": None,
                "openai_api_key": None,
                "translate": False,
                "clean_after_days": current_user_settings.clean_after_days,
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
                clean_after_days=current_user_settings.clean_after_days,
            ),
            200,
        )


@api_settings_blueprint.route("/daily", methods=["GET", "POST"])
def daily_settings():
    # Get the current user from the session
    if not current_user.is_authenticated:
        return jsonify({"message": "User not authenticated."}), 401

    # Query the database for the settings of the current user
    current_user_settings = Settings.query.filter_by(
        user_id=current_user.id
    ).first()
    user = User.query.filter_by(id=current_user.id).first()

    if user.daily_sync_at is None:
        now = datetime.now(UTC)
        user.daily_sync_at = now.replace(
            hour=7, minute=0, second=0, microsecond=0
        )
        if now.hour >= 7:
            user.daily_sync_at += timedelta(days=1)

    if user.daily_sync_at.tzinfo is None:
        user.daily_sync_at = pytz.utc.localize(user.daily_sync_at)

    user_timezone = pytz.timezone(current_user_settings.timezone)
    daily_sync_at_user_tz = user.daily_sync_at.astimezone(user_timezone)
    daily_sync_at = daily_sync_at_user_tz.strftime("%H:%M:%S")

    if request.method == "GET":
        feeds = Feed.query.filter_by(user_id=current_user.id).all()
        feed_output = [feed.to_dict() for feed in feeds]

        # Return the user's settings in a JSON format
        return (
            jsonify(
                active=current_user_settings.daily_active,
                hours_summary=current_user_settings.daily_hours_summary,
                translate=current_user_settings.daily_translate,
                last_sync_time_duration=(
                    current_user_settings.daily_last_sync_time_duration
                ),
                process_read=current_user_settings.daily_process_read,
                title_provider=current_user_settings.daily_title_provider,
                compare_titles=current_user_settings.daily_compare_titles,
                daily_sync_at=daily_sync_at,
                feeds=feed_output,
            ),
            200,
        )

    elif request.method == "POST":
        # Update the settings of the current user based on the
        # data received from the POST request
        active = request.json.get("active")
        hours_summary = request.json.get("hours_summary")
        translate = request.json.get("translate")
        process_read = request.json.get("process_read")
        compare_titles = request.json.get("compare_titles")
        title_provider = request.json.get("title_provider")

        sync_at = request.json.get("sync_at")
        sync_time = datetime.strptime(sync_at, "%H:%M:%S").time()
        current_date = datetime.now(user_timezone).date()
        sync_datetime_user_tz = datetime.combine(current_date, sync_time)
        sync_datetime_user_tz = user_timezone.localize(sync_datetime_user_tz)
        sync_datetime_utc = sync_datetime_user_tz.astimezone(pytz.utc)

        current_user_settings.daily_active = (
            active
            if active is not None
            else current_user_settings.daily_active
        )
        current_user_settings.daily_hours_summary = (
            hours_summary
            if hours_summary is not None
            else current_user_settings.daily_hours_summary
        )
        current_user_settings.daily_translate = (
            translate
            if translate is not None
            else current_user_settings.daily_translate
        )
        current_user_settings.daily_process_read = (
            process_read
            if process_read is not None
            else current_user_settings.daily_process_read
        )

        current_user_settings.daily_compare_titles = (
            compare_titles
            if compare_titles is not None
            else current_user_settings.daily_compare_titles
        )

        current_user_settings.daily_title_provider = (
            title_provider
            if title_provider is not None
            else current_user_settings.daily_title_provider
        )

        user.daily_sync_at = (
            sync_datetime_utc
            if sync_datetime_utc is not None
            else user.daily_sync_at
        )

        try:
            db.session.commit()
        except Exception as e:
            logging.error(
                "Error updating settings for %s: %s", current_user, str(e)
            )
            db.session.rollback()
            return (
                jsonify(
                    message=f"Error updating settings for {current_user}: {e}"
                ),
                500,
            )
        return (jsonify(message="Settings updated successfully"), 200)


@api_settings_blueprint.route("/daily/feed", methods=["PUT"])
def update_daily_feed():
    """Update daily feed settings."""
    if not current_user.is_authenticated:
        return jsonify({"message": "User not authenticated."}), 401

    if request.method == "PUT":
        feed = request.get_json()
        print(feed)
        feed_id = feed.get("id")
        daily_enabled = feed.get("dailyEnabled")
        if feed_id is None:
            return jsonify({"message": "Missing feed ID."}), 400

        # Fetch the feed by ID
        existing_feed = Feed.query.filter_by(id=feed_id).first()

        if not existing_feed:
            return jsonify({"message": "Feed not found."}), 404

        # Update the feed's active status
        existing_feed.daily_enabled = daily_enabled

        try:
            db.session.commit()
        except Exception as e:
            logging.error("Error updating feed %s: %s", feed_id, str(e))
            db.session.rollback()
            return (jsonify(message=f"Error updating feed: {str(e)}"), 500)

        return jsonify(message="Feed updated successfully"), 200


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
                    "error": (
                        "New password must be different from the old password"
                    )
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
