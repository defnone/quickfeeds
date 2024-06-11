import pytz
from flask import Blueprint, redirect, render_template, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Category, Feed, Settings
from app.utils.version import get_version

routes_blueprint = Blueprint("routes", __name__)


def get_user_settings(user_id):
    """
    Retrieve user settings for the given user ID.
    """
    return Settings.query.filter_by(user_id=user_id).first()


@routes_blueprint.route("/")
@login_required
def index():
    """
    Render the index page or redirect to 'all_items' if no unread items.
    """
    user_settings = get_user_settings(current_user.id)
    if not user_settings.unread:
        return redirect(url_for("routes.all_items"))
    return render_template("index.html", title="All Unread feeds")


@routes_blueprint.route("/all")
@login_required
def all_items():
    """
    Render the 'all items' page or redirect to 'index' if unread items exist.
    """
    user_settings = get_user_settings(current_user.id)
    if user_settings.unread:
        return redirect(url_for("routes.index"))
    return render_template("index.html", title="All feeds")


@routes_blueprint.route("/category/<int:cat_id>")
@login_required
def category_items(cat_id):
    """
    Render category items or redirect to 'all_category_items' if no unread items.
    """
    user_settings = get_user_settings(current_user.id)
    if not user_settings.unread:
        return redirect(url_for("routes.all_category_items", cat_id=cat_id))
    category = db.session.get(Category, cat_id)
    if not category:
        flash(("Category not found.", "error"))
        return redirect(url_for("routes.index"))
    return render_template(
        "index.html", title=f"Unread {category.name} category"
    )


@routes_blueprint.route("/category/<int:cat_id>/all")
@login_required
def all_category_items(cat_id):
    """
    Render all category items or redirect to 'category_items' if unread items exist.
    """
    user_settings = get_user_settings(current_user.id)
    if user_settings.unread:
        return redirect(url_for("routes.category_items", cat_id=cat_id))
    category = db.session.get(Category, cat_id)
    if not category:
        flash(("Category not found.", "error"))
        return redirect(url_for("routes.index"))
    return render_template("index.html", title=f"All {category.name} category")


@routes_blueprint.route("/category/<int:cat_id>/feed/<int:feed_id>")
@login_required
def feed_items(cat_id, feed_id):
    """
    Render feed items or redirect to 'all_feed_items' if no unread items.
    """
    user_settings = get_user_settings(current_user.id)
    if not user_settings.unread:
        return redirect(
            url_for("routes.all_feed_items", cat_id=cat_id, feed_id=feed_id)
        )
    feed = db.session.get(Feed, feed_id)
    if not feed:
        flash(("Feed not found.", "error"))
        return redirect(url_for("routes.index"))
    title = f"Unread {feed.title}"
    return render_template("index.html", title=title)


@routes_blueprint.route("/category/<int:cat_id>/feed/<int:feed_id>/all")
@login_required
def all_feed_items(cat_id, feed_id):
    """
    Render all feed items or redirect to 'feed_items' if unread items exist.
    """
    user_settings = get_user_settings(current_user.id)
    if user_settings.unread:
        return redirect(
            url_for("routes.feed_items", cat_id=cat_id, feed_id=feed_id)
        )
    feed = db.session.get(Feed, feed_id)
    if not feed:
        flash(("Feed not found.", "error"))
        return redirect(url_for("routes.index"))
    title = f"All {feed.title}"
    return render_template("index.html", title=title)


@routes_blueprint.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """
    Render the settings page.
    """
    version = get_version()
    return render_template(
        "settings.html",
        title="Settings",
        timezones=pytz.all_timezones,
        version=version,
    )


@routes_blueprint.route("/settings/categories", methods=["GET"])
@login_required
def settings_categories():
    """
    Render the settings page.
    """
    return render_template(
        "settings-manage-cat.html",
        title="Manage Categories",
    )
