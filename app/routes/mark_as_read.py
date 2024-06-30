from flask import Blueprint, jsonify, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import update, select
from app.extensions import db
from app.models import Feed, FeedItem, ArticleLink, SummarizedArticle

mark_as_read_blueprint = Blueprint("mark_as_read", __name__)


@mark_as_read_blueprint.route("/mark_as_read/<int:item_id>", methods=["POST"])
@login_required
def mark_as_read(item_id):
    """
    Marks a feed item as read.

    Args:
        item_id (int): The ID of the feed item to mark as read.

    Returns:
        redirect: A redirect response to the index page.
    """
    item = db.session.get(FeedItem, item_id)
    if item is None:
        return jsonify({"status": "error", "message": "Item not found"}), 404

    item.read = True
    db.session.commit()
    return jsonify({"status": "success"})


@mark_as_read_blueprint.route("/all/mark_as_read_all", methods=["POST"])
@mark_as_read_blueprint.route("/mark_as_read_all", methods=["POST"])
@login_required
def mark_as_read_all():
    """
    Marks all items as read for the current user.

    This function retrieves the IDs of all feeds belonging to the current user,
    and then updates the 'read' attribute of all feed items associated with
    those feeds to True.

    Returns:
        A redirect response to the index page.
    """
    subquery = (
        db.session.query(Feed.id)
        .filter(Feed.user_id == current_user.id)
        .subquery()
    )
    stmt = (
        update(FeedItem)
        .where(FeedItem.feed_id.in_(select(subquery)))
        .values(read=True)
    )
    db.session.execute(stmt)
    db.session.commit()
    return redirect(url_for("routes.index"))


@mark_as_read_blueprint.route(
    "/category/<int:cat_id>/mark_as_read_all", methods=["POST"]
)
@mark_as_read_blueprint.route(
    "/category/<int:cat_id>/all/mark_as_read_all", methods=["POST"]
)
@login_required
def mark_as_read_all_category(cat_id):
    """
    Marks all items in a category as read for the current user.

    This function retrieves the IDs of all feeds belonging to the current user and the specified category,
    and then updates the 'read' attribute of all feed items associated with
    those feeds to True.

    Returns:
        A redirect response to the category page.
    """
    subquery = (
        db.session.query(Feed.id)
        .filter(Feed.user_id == current_user.id, Feed.category_id == cat_id)
        .subquery()
    )
    stmt = (
        update(FeedItem)
        .where(FeedItem.feed_id.in_(select(subquery)))
        .values(read=True)
    )
    db.session.execute(stmt)
    db.session.commit()
    return redirect(url_for("routes.all_category_items", cat_id=cat_id))


@mark_as_read_blueprint.route(
    "/category/<int:cat_id>/feed/<int:feed_id>/mark_as_read_all",
    methods=["POST"],
)
@mark_as_read_blueprint.route(
    "/category/<int:cat_id>/feed/<int:feed_id>/all/mark_as_read_all",
    methods=["POST"],
)
@login_required
def mark_as_read_all_feed(cat_id, feed_id):
    """
    Marks all items in a feed as read for the current user.

    This function updates the 'read' attribute of all feed items associated with
    the specified feed to True.

    Returns:
        A redirect response to the feed page.
    """
    stmt = (
        update(FeedItem).where(FeedItem.feed_id == feed_id).values(read=True)
    )
    db.session.execute(stmt)
    db.session.commit()
    return redirect(
        url_for("routes.all_feed_items", cat_id=cat_id, feed_id=feed_id)
    )


@mark_as_read_blueprint.route(
    "/mark_as_read/daily/<int:item_id>", methods=["POST"]
)
@login_required
def mark_as_read_daily(item_id):
    """
    Marks a feed item as read.

    Args:
        item_id (int): The ID of the feed item to mark as read.

    Returns:
        redirect: A redirect response to the index page.
    """
    summarized_article = db.session.get(SummarizedArticle, item_id)
    if summarized_article is None:
        return (
            jsonify(
                {"status": "error", "message": "Summarized article not found"}
            ),
            404,
        )

    # Mark SummarizedArticle as read
    summarized_article.read = True
    db.session.commit()

    # Mark associated FeedItems as read through ArticleLink
    article_links = ArticleLink.query.filter_by(
        summarized_article_id=item_id
    ).all()
    for article_link in article_links:
        feed_item = article_link.original_article
        feed_item.read = True
        db.session.commit()

    return jsonify({"status": "success"})
