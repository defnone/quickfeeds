import logging
from flask import Blueprint, jsonify, request
from flask_login import current_user
import pytz
from sqlalchemy.exc import SQLAlchemyError
from app.models import Settings, Feed, FeedItem
from app.utils.serialization import serialize_item

api_feeditems_blueprint = Blueprint("api_feeditems_blueprint", __name__)


def get_user_timezone():
    """
    Retrieve the user's timezone from settings. If not found, default to UTC.
    """
    user_settings = Settings.query.filter_by(user_id=current_user.id).first()
    return pytz.timezone(user_settings.timezone) if user_settings else pytz.utc


def get_items(query, limit, last_item_id):
    """
    Fetch a limited number of items based on the query and last item ID for
    pagination.

    Parameters:
    - query: SQLAlchemy query object
    - limit: Number of items to retrieve
    - last_item_id: ID of the last item from the previous request for
    pagination

    Returns:
    - List of FeedItem objects
    """
    if last_item_id:
        try:
            last_item = FeedItem.query.get(last_item_id)
            query = query.filter(
                (FeedItem.pub_date < last_item.pub_date)
                | (
                    (FeedItem.pub_date == last_item.pub_date)
                    & (FeedItem.id < last_item.id)
                )
            )
        except SQLAlchemyError as e:
            logging.error(f"Error fetching last item: {e}")
            return []
    try:
        items = query.limit(limit).all()
    except SQLAlchemyError as e:
        logging.error(f"Error fetching items: {e}")
        return []
    return items


def create_response(items, user_timezone):
    """
    Create a JSON response with serialized items.

    Parameters:
    - items: List of FeedItem objects
    - user_timezone: User's timezone for serialization

    Returns:
    - JSON response with serialized items
    """
    item_ids = [item.id for item in items]
    logging.debug(f"Returned item IDs: {item_ids}")
    return jsonify([serialize_item(item, user_timezone) for item in items])


@api_feeditems_blueprint.route("", methods=["GET"])
def get_feed_items():
    """
    Retrieve unread feed items for the current user with optional pagination.

    Query parameters:
    - limit: Maximum number of items to retrieve (default: 5)
    - last_item_id: ID of the last item from the previous request for
    pagination

    Returns:
    - JSON response with serialized unread feed items
    """
    if not current_user.is_authenticated:
        return (
            jsonify({"status": "error", "error": "User not authenticated"}),
            401,
        )

    limit = int(request.args.get("limit", 5))
    last_item_id = request.args.get("last_item_id")
    user_timezone = get_user_timezone()

    query = (
        FeedItem.query.join(Feed, Feed.id == FeedItem.feed_id)
        .filter(Feed.user_id == current_user.id, FeedItem.read == False)
        .order_by(FeedItem.pub_date.desc())
    )

    items = get_items(query, limit, last_item_id)
    return create_response(items, user_timezone)


@api_feeditems_blueprint.route("/all", methods=["GET"])
def get_all_feed_items():
    """
    Retrieve all feed items for the current user with optional pagination.

    Query parameters:
    - limit: Maximum number of items to retrieve (default: 5)
    - last_item_id: ID of the last item from the previous request for
    pagination

    Returns:
    - JSON response with serialized feed items
    """
    if not current_user.is_authenticated:
        return (
            jsonify({"status": "error", "error": "User not authenticated"}),
            401,
        )

    limit = int(request.args.get("limit", 5))
    last_item_id = request.args.get("last_item_id")
    user_timezone = get_user_timezone()

    query = FeedItem.query.order_by(FeedItem.pub_date.desc())

    items = get_items(query, limit, last_item_id)
    return create_response(items, user_timezone)


@api_feeditems_blueprint.route("/<int:cat_id>", methods=["GET"])
def get_category_feed_items(cat_id):
    """
    Retrieve unread feed items for a specific category and the current user
    with optional pagination.

    Parameters:
    - cat_id: Category ID

    Query parameters:
    - limit: Maximum number of items to retrieve (default: 5)
    - last_item_id: ID of the last item from the previous request for
    pagination

    Returns:
    - JSON response with serialized unread feed items in the specified category
    """
    if not current_user.is_authenticated:
        return (
            jsonify({"status": "error", "error": "User not authenticated"}),
            401,
        )

    limit = int(request.args.get("limit", 5))
    last_item_id = request.args.get("last_item_id")
    user_timezone = get_user_timezone()

    query = (
        FeedItem.query.join(Feed, Feed.id == FeedItem.feed_id)
        .filter(
            Feed.category_id == cat_id,
            Feed.user_id == current_user.id,
            FeedItem.read == False,
        )
        .order_by(FeedItem.pub_date.desc())
    )

    items = get_items(query, limit, last_item_id)
    return create_response(items, user_timezone)


@api_feeditems_blueprint.route("/<int:cat_id>/all", methods=["GET"])
def get_all_category_feed_items(cat_id):
    """
    Retrieve all feed items for a specific category and the current user with
    optional pagination.

    Parameters: - cat_id: Category ID

    Query parameters: - limit: Maximum number of items to retrieve (default: 5)
    - last_item_id: ID of the last item from the previous request for
    pagination

    Returns: - JSON response with serialized feed items in the specified
    category
    """
    if not current_user.is_authenticated:
        return (
            jsonify({"status": "error", "error": "User not authenticated"}),
            401,
        )

    limit = int(request.args.get("limit", 5))
    last_item_id = request.args.get("last_item_id")
    user_timezone = get_user_timezone()

    query = (
        FeedItem.query.join(Feed, Feed.id == FeedItem.feed_id)
        .filter(Feed.category_id == cat_id)
        .order_by(FeedItem.pub_date.desc())
    )

    items = get_items(query, limit, last_item_id)
    return create_response(items, user_timezone)


@api_feeditems_blueprint.route("/<int:cat_id>/<int:feed_id>", methods=["GET"])
def get_specific_feed_items(cat_id, feed_id):
    """
    Retrieve unread feed items for a specific feed within a category for the
    current user with optional pagination.

    Parameters: - cat_id: Category ID - feed_id: Feed ID

    Query parameters: - limit: Maximum number of items to retrieve (default: 5)
    - last_item_id: ID of the last item from the previous request for
    pagination

    Returns: - JSON response with serialized unread feed items in the specified
    feed
    """
    if not current_user.is_authenticated:
        return (
            jsonify({"status": "error", "error": "User not authenticated"}),
            401,
        )

    limit = int(request.args.get("limit", 5))
    last_item_id = request.args.get("last_item_id")
    user_timezone = get_user_timezone()

    query = (
        FeedItem.query.join(Feed, Feed.id == FeedItem.feed_id)
        .filter(
            Feed.category_id == cat_id,
            Feed.id == feed_id,
            Feed.user_id == current_user.id,
            FeedItem.read == False,
        )
        .order_by(FeedItem.pub_date.desc())
    )

    items = get_items(query, limit, last_item_id)
    return create_response(items, user_timezone)


@api_feeditems_blueprint.route(
    "/<int:cat_id>/<int:feed_id>/all", methods=["GET"]
)
def get_all_specific_feed_items(cat_id, feed_id):
    """
    Retrieve all feed items for a specific feed within a category for the
    current user with optional pagination.

    Parameters:
    - cat_id: Category ID
    - feed_id: Feed ID

    Query parameters:
    - limit: Maximum number of items to retrieve (default: 5)
    - last_item_id: ID of the last item from the previous request for
    pagination

    Returns:
    - JSON response with serialized feed items in the specified feed
    """
    if not current_user.is_authenticated:
        return (
            jsonify({"status": "error", "error": "User not authenticated"}),
            401,
        )

    limit = int(request.args.get("limit", 5))
    last_item_id = request.args.get("last_item_id")
    user_timezone = get_user_timezone()

    query = (
        FeedItem.query.join(Feed, Feed.id == FeedItem.feed_id)
        .filter(Feed.category_id == cat_id, Feed.id == feed_id)
        .order_by(FeedItem.pub_date.desc())
    )

    items = get_items(query, limit, last_item_id)
    return create_response(items, user_timezone)
