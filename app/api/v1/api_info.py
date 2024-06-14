from datetime import datetime
from flask import Blueprint, jsonify
from flask_login import current_user
import humanize
import pytz
from app.models import Category, Feed, FeedItem, User, Settings

api_ui_info_blueprint = Blueprint("api", __name__)


@api_ui_info_blueprint.route("/categories_and_blogs", methods=["GET"])
def get_categories_and_blogs():
    """
    Returns categories and associated feeds with unread counts.

    Returns:
        dict: A dictionary containing categories and associated feeds
        with unread counts.
    """
    if current_user.is_authenticated:
        categories = Category.query.all()
        data = []

        for cat in categories:
            feeds = Feed.query.filter_by(category_id=cat.id).all()
            feed_data = []

            for feed in feeds:
                unread_count = FeedItem.query.filter_by(
                    feed_id=feed.id, read=False
                ).count()
                feed_data.append(
                    {"feed": feed.to_dict(), "unread_count": unread_count}
                )

            cat_data = {"id": cat.id, "name": cat.name, "feeds": feed_data}
            data.append(cat_data)

        return jsonify({"categories_and_blogs": data})
    else:
        return jsonify({})


@api_ui_info_blueprint.route("/last_sync", methods=["GET"])
def get_last_sync():
    """
    Returns the last sync time.

    Returns:
        dict: A dictionary containing the last sync time.
    """
    if current_user.is_authenticated:
        user = User.query.filter_by(id=current_user.id).first()
        if user and user.last_sync is not None:
            settings = Settings.query.filter_by(user_id=user.id).first()
            if settings and settings.timezone:
                user_tz = pytz.timezone(settings.timezone)
                user_last_sync = user_tz.localize(user.last_sync)
            else:
                # Ensure user_last_sync is aware
                if user.last_sync.tzinfo is None:
                    user_last_sync = pytz.utc.localize(user.last_sync)
                else:
                    user_last_sync = user.last_sync

            last_sync_time = humanize.naturaltime(
                datetime.now(pytz.utc) - user_last_sync
            )
            return jsonify({"last_sync": last_sync_time})
        else:
            return jsonify({"last_sync": "Never"})
    else:
        return jsonify({})


@api_ui_info_blueprint.route("/unread-count")
def unread_count():
    if current_user.is_authenticated:
        unread_items_count = (
            FeedItem.query.join(Feed)
            .filter(Feed.user_id == current_user.id, FeedItem.read == False)
            .count()
        )
        return jsonify(unread_count=unread_items_count)
    return jsonify(unread_count=0)
