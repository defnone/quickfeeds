import logging
import pytz
from flask import Blueprint, jsonify, request, session
from flask_login import current_user
from app.models import SummarizedArticle, ArticleLink, FeedItem, Settings, Feed
from app import db
from app.utils.text import get_text_from_url, text_to_html_list
from app.utils.groq import groq_request
from app.utils.promts import SUMMARIZE


api_daily_blueprint = Blueprint("api_daily_blueprint", __name__)


def get_user_timezone():
    user_settings = Settings.query.filter_by(user_id=current_user.id).first()
    return pytz.timezone(user_settings.timezone) if user_settings else pytz.utc


@api_daily_blueprint.route("/feed", methods=["GET"])
def daily_feed():
    """
    Endpoint that retrieves a daily feed of summarized articles for the
    authenticated user. It allows paginated results based on the specified
    limit and the last item ID to determine which articles to fetch.

    The function processes requests to filter by unread articles and
    manages a session-based tracking of already issued articles to avoid
    duplication in results.

    Query Parameters:
    - limit (int): Maximum number of articles to retrieve. Default is 10.
    - last_item_id (int): ID of the last retrieved summarized article,
      used for pagination.
    - unread (bool): If provided, filters the results to only include
      unread articles.
    Returns:
    - A JSON response containing a list of dictionaries, each representing
      a summarized article, with details such as summary, image link,
      associated original articles, publication date converted to the
      user's timezone, and read status.

    Responses:
    - 401: User not authenticated
    - 200: Successful retrieval of articles with summary details
    """
    if not current_user.is_authenticated:
        return (
            jsonify({"status": "error", "error": "User not authenticated"}),
            401,
        )

    limit = int(request.args.get("limit", 10))
    last_item_id = request.args.get("last_item_id")
    unread = request.args.get("unread")

    query = (
        db.session.query(SummarizedArticle)
        .join(ArticleLink)
        .join(FeedItem)
        .order_by(
            SummarizedArticle.pub_date.desc(), SummarizedArticle.id.desc()
        )
    )

    if not last_item_id:
        session["issued_articles"] = []

    issued_articles = set(session.get("issued_articles", []))

    if last_item_id:
        last_item = (
            db.session.query(SummarizedArticle)
            .filter_by(id=last_item_id)
            .first()
        )
        if last_item and last_item.original_articles:
            first_article = last_item.original_articles[0].original_article
            if first_article:
                last_item_pub_date = first_article.pub_date
                if last_item_pub_date:
                    query = query.filter(
                        (SummarizedArticle.pub_date < last_item_pub_date)
                        | (
                            (SummarizedArticle.pub_date == last_item_pub_date)
                            & (SummarizedArticle.id < last_item.id)
                        )
                    )

    if unread:
        query = query.filter(SummarizedArticle.read == False)

    summarized_articles = query.limit(limit * 2).all()

    result = []
    new_issued_articles = list(issued_articles)

    for summarized_article in summarized_articles:
        if summarized_article.id in issued_articles:
            continue

        article_links = summarized_article.original_articles
        titles_and_links = []

        for article_link in article_links:
            feed_item = article_link.original_article
            if not feed_item:
                continue

            naive_datetime_utc = feed_item.pub_date
            if naive_datetime_utc and naive_datetime_utc.tzinfo:
                naive_datetime_utc = naive_datetime_utc.replace(tzinfo=None)

            user_timezone = get_user_timezone()
            datetime_in_user_tz = (
                pytz.utc.localize(naive_datetime_utc).astimezone(user_timezone)
                if naive_datetime_utc
                else None
            )

            feed_id = feed_item.feed_id
            feed_title = Feed.query.get(feed_id).title
            titles_and_links.append(
                {
                    "title": feed_item.title,
                    "link": feed_item.link,
                    "feed_id": feed_id,
                    "feed_title": feed_title,
                }
            )

        result.append(
            {
                "summary": summarized_article.summary,
                "image": summarized_article.image_link,
                "articles": titles_and_links,
                "id": summarized_article.id,
                "pub_date": (
                    datetime_in_user_tz.isoformat()
                    if datetime_in_user_tz
                    else None
                ),
                "created_at": summarized_article.created_at,
                "read": summarized_article.read,
            }
        )

        new_issued_articles.append(summarized_article.id)
        if len(result) >= limit:
            break

    if len(summarized_articles) < limit * 2:
        new_issued_articles = []

    session["issued_articles"] = new_issued_articles

    return jsonify(result)


@api_daily_blueprint.route("/summarize/<int:id>", methods=["GET", "POST"])
def summarize_article(id):
    """
    Endpoint that summarizes a specified article for the authenticated user.
    This function fetches the article's content from its URL and processes it
    to create a summary using the Groq API. It can also translate the summary
    into the user's preferred language if translation is enabled in the user's
    settings.

    Parameters:
    - id (int): The ID of the article to summarize.

    Returns:
    - A JSON response containing the summarized text of the article or error
      messages in case of failure. The response also includes the status of
      the operation.

    Responses:
    - 401: User not authenticated
    - 403: Missing API key
    - 404: Article not found
    - 400: Failed to get text from URL
    - 500: Failed to summarize or translate the article

    Workflow:
    1. Check if the user is authenticated.
    2. Retrieve the user's settings and check if a Groq API key is available.
    3. Fetch the specified article by its ID. If the article is found:
        - Extract its original article links.
        - Attempt to get the text content from the first article's URL.
        - Use Groq API for summarization of the content. Handle errors if they
          arise during this operation.
        - If translation is enabled, translate the summary using Google's
          translation services.
    4. Return the summarized article in the response, or handle errors
       appropriately.
    """
    if not current_user.is_authenticated:
        return (jsonify(status="error", error="User not authenticated"), 401)

    current_user_settings = Settings.query.filter_by(
        user_id=current_user.id
    ).first()

    if not current_user_settings.groq_api_key:
        return jsonify({"status": "error", "error": "Missing API key"}), 403

    summarized_article = SummarizedArticle.query.get(id)
    if summarized_article:
        original_articles = summarized_article.original_articles
        for article_link in original_articles:
            feed_item = article_link.original_article
            url = feed_item.link
            query = get_text_from_url(url, processor="goose3")

            if not query:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "error": "Failed to get text from URL",
                        }
                    ),
                    400,
                )
            try:
                response = groq_request(
                query,
                current_user_settings.groq_api_key,
                    SUMMARIZE
                    + "\n\nThe summary must be written in "
                    + current_user_settings.language,
                    model="llama-4-maverick-17b-128e-instruct",
                )

                break
            except Exception as e:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "error": f"Failed to summarize: {str(e)}",
                        }
                    ),
                    500,
                )
        
    else:
        logging.error("Article not found")
        return jsonify({"status": "error", "error": "Article not found"}), 404
    logging.debug(response)
    response = text_to_html_list(response)
    return jsonify({"summary": response}), 200
