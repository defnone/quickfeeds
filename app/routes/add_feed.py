from datetime import datetime
import logging
import feedparser
import feedfinder2
from dateutil import parser
from flask import Blueprint, flash, jsonify, redirect, request, url_for
from flask_login import login_required, current_user
import pytz
from app.utils.cleaner import clean_summary
from app.utils.tz import tzinfos
from app.extensions import db
from app.models import Category, Feed, FeedItem


add_feed_blueprint = Blueprint("add_feed_route", __name__)


def is_feed(url):
    feed = feedparser.parse(url)
    if feed.bozo:
        print(f"FeedParser bozo: {feed.bozo_exception}")
        return False
    if "entries" in feed and len(feed.entries) > 0:
        return True
    return False


@add_feed_blueprint.route("/add_feed", methods=["POST"])
@login_required
def add_feed():
    """
    This function handles the POST request to add a new feed. It first checks
    if the site URL is provided. If not, it redirects to the index page. If the
    site URL is provided, it tries to find the RSS feed from the site. If the
    feed is found, it checks if the feed already exists in the database. If it
    does, it returns an error. If the feed does not exist, it adds the feed to
    the database. It also checks if a category is provided. If a category is
    provided, it checks if the category already exists. If it does, it uses the
    existing category. If it does not, it creates a new category. It then
    parses the feed and adds each entry to the database. If the feed is
    successfully added, it returns a success message. If there is an error, it
    returns an error message.
    """
    success = False
    try:
        # Check if site URL is provided
        if "site_url" not in request.form:
            flash(("No site URL provided.", "error"))
            return redirect(url_for("routes.index"))

        site_url = request.form["site_url"]
        category_name = request.form.get("category")

        if site_url.startswith("http://"):
            site_url = "https://" + site_url.split("http://")[1]
        elif not site_url.startswith("https://"):
            site_url = "https://" + site_url

        # Log the received site URL and category name
        logging.info("Received site_url: %s", site_url)
        logging.info("Received category_name: %s", category_name)

        # Find the RSS feed from the site URL
        if not is_feed(site_url):
            feeds = feedfinder2.find_feeds(site_url)
            if not feeds:
                return jsonify(
                    {
                        "success": False,
                        "error": "RSS feed not found on the website",
                    }
                )
        else:
            feeds = [site_url]

        feed_url = feeds[0]

        # if feed_url and not is_feed(feed_url):
        #     logging.error("Invalid RSS feed: %s", feed_url)
        #     return jsonify(
        #         {
        #             "success": False,
        #             "error": "Invalid RSS feed",
        #         }
        #     )

        # Check if the feed already exists in the database
        existing_feed = Feed.query.filter_by(url=feed_url).first()
        if existing_feed:
            return jsonify(
                {
                    "success": False,
                    "error": "Feed already exists in the database",
                }
            )

        # Check if a category is provided and if it exists
        if category_name:
            existing_category = Category.query.filter_by(
                name=category_name
            ).first()
            if not existing_category:
                # If the category does not exist, create a new category
                new_category = Category(
                    name=category_name, user_id=current_user.id
                )
                db.session.add(new_category)
                db.session.commit()
                category_name = new_category
            else:
                category_name = existing_category
        else:
            category_name = None

        # Parse the feed and add each entry to the database
        feed_data = feedparser.parse(feed_url, sanitize_html=False)
        feed_title = feed_data.feed.get("title", "No title")

        feed = Feed(
            url=feed_url,
            title=feed_title,
            user_id=current_user.id,
            category_id=category_name.id if category_name else None,
        )
        db.session.add(feed)
        db.session.commit()

        for entry in feed_data.entries:
            enclosure_html = ""

            # Handle enclosures in the feed entry
            if "enclosures" in entry:
                for enclosure in entry.enclosures:
                    url = enclosure.get("url")
                    type_ = enclosure.get("type")

                    if type_ and url:
                        if type_.startswith("image/"):
                            enclosure_html += (
                                f'<img src="{url}" alt="Enclosure Image">'
                            )
                        elif type_.startswith("audio/"):
                            enclosure_html += (
                                f'<audio controls src="{url}"></audio>'
                            )
                        elif type_.startswith("video/"):
                            enclosure_html += (
                                f'<video controls src="{url}"></video>'
                            )

            # Handle media content in the feed entry
            media_content_html = ""
            if "media_content" in entry:

                for media_content in entry.media_content:
                    url = media_content.get("url")
                    medium = media_content.get("medium")

                    if url and medium == "image":
                        media_content_html += f'<img src="{url}">'
                        break

            # Handle the content of the feed entry
            summary = ""
            if "content" in entry and len(entry["content"][0]["value"]) > 0:
                summary = entry["content"][0]["value"]
            elif "description" in entry:
                summary = entry["description"]
            elif "summary" in entry:
                summary = entry["summary"]
            else:
                summary = ""

            summary = media_content_html + enclosure_html + summary
            summary = clean_summary(summary)

            # Handle the publication date of the feed entry
            pub_date = None
            if hasattr(entry, "published_parsed"):
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed"):
                pub_date = datetime(*entry.updated_parsed[:6])
            else:
                pub_date_str = entry.get("published") or entry.get("updated")
                if pub_date_str:
                    pub_date = parser.parse(pub_date_str, tzinfos=tzinfos)
                    if pub_date.tzinfo is None:
                        pub_date = pytz.utc.localize(pub_date)
                    else:
                        pub_date = pub_date.astimezone(pytz.utc)

            # Handle the author of the feed entry
            creator = entry.get("author") or (
                entry.get("authors")[0]["name"]
                if entry.get("authors")
                else None
            )

            # Add the feed entry to the database if it does not already exist
            if not FeedItem.query.filter_by(link=entry.link).first():
                item = FeedItem(
                    title=entry.title,
                    link=entry.link,
                    summary=summary,
                    pub_date=pub_date,
                    creator=creator,
                    feed_id=feed.id,
                )
                db.session.add(item)
                success = True

        db.session.commit()

        # Return a success message if the feed is successfully added
        if success:
            flash(("Feed added successfully", "success"))
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Error adding feed"})
    except Exception as e:
        # Return an error message if there is an error
        return jsonify(
            {"success": False, "error": f"Error adding feed: {str(e)}"}
        )
