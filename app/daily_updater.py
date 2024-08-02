import re
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd
import nltk
from bs4 import BeautifulSoup
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

# Internal modules imports
from app import db, create_app
from app.models import (
    Feed,
    FeedItem,
    SummarizedArticle,
    ArticleLink,
    Settings,
    User,
)
from app.utils.text import get_text_from_url, get_image_from_url
from app.utils.groq import groq_compare_titles, groq_request
from app.utils.chatgpt import openai_compare_titles
from app.utils.promts import COMPARE_TITLES, SUMMARIZE_ONE
from app.utils.translate import translate_text_google

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download NLTK data if not downloaded yet
nltk.download("punkt", quiet=True)

app = create_app(db)
with app.app_context():
    settings = Settings.query.join(User).order_by(User.id).first()


def clean_text(text: str) -> str:
    patterns = (
        r"read more.*?(?=\.\s|$)",
        r"also read.*?(?=\.\s|$)",
        r"related articles.*?(?=\.\s|$)",
    )
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text


def extract_first_image_link_from_summary(summary: str, link: str) -> str:
    soup = BeautifulSoup(summary, "html.parser")
    img_tag = soup.find("img")
    if img_tag and "src" in img_tag.attrs:
        return img_tag["src"]

    try:
        return get_image_from_url(link)
    except Exception as e:
        logger.warning(
            "Failed to fetch image from URL: %s, Error: %s", link, e
        )
        return None


def extract_summary(text: str, num_sentences: int = 10) -> str:
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = TextRankSummarizer()
    summary = summarizer(parser.document, num_sentences)
    summary_sentences = [str(sentence) for sentence in summary]
    return " ".join(summary_sentences)


def create_summary(
    cluster: list[int], df: pd.DataFrame, num_sentences: int = 10
) -> tuple[str, list[str]]:
    summaries = []
    image_links = []
    for idx in cluster:
        link = df.iloc[idx]["link"]
        summary_text = df.iloc[idx]["summary"]
        try:
            text = clean_text(summary_text)
            summary = extract_summary(text, num_sentences)
            image_link = extract_first_image_link_from_summary(
                summary_text, link
            )
            summaries.append(
                f"{df.iloc[idx]['title']}\nSummary: {summary}\nLink: {link}"
            )
            image_links.append(image_link)
            logger.info(
                "Processed article: %s %s", df.iloc[idx]["title"], link
            )
        except Exception as e:
            summaries.append(
                f"{df.iloc[idx]['title']}\nSummary: Failed to fetch text.\nLink: {link}"
            )
            image_links.append(None)
            logger.error(
                "Failed to process article:\n%(title)s\nLink: %(link)s\nError: %(error)s",
                {"title": df.iloc[idx]["title"], "link": link, "error": e},
            )

    return "\n\n".join(summaries), image_links


def summarize_batched_text(
    summaries: list[str], titles_and_links: list[str]
) -> dict:
    api_key = settings.groq_api_key
    result_dict = {}
    max_retries = 12

    def fetch_summary(title: str, text: str, attempt: int = 1) -> str:
        logger.info("Sending to API: %s", (title, text))
        try:
            response = groq_request(
                (title, text), api_key, SUMMARIZE_ONE, True, "8b"
            )
            logger.info("Response from API: %s", response)
            if (
                isinstance(response, dict)
                and "error" in response
                and response["error"] == "No JSON object found in the response"
            ):
                if attempt < max_retries:
                    logger.warning(
                        "Retrying due to error: %s", response["error"]
                    )
                    return fetch_summary(title, text, attempt + 1)
                else:
                    logger.error("Max retries reached for title: %s", title)
                    return None
            if isinstance(response, str) and response.startswith(
                "Here is a summary"
            ):
                response = response.split(":", 1)[1].strip()
            return response
        except Exception as e:
            logger.error("Error while sending to Groq API: %s", e)
            if attempt < max_retries:
                logger.warning("Retrying due to exception: %s", e)
                return fetch_summary(title, text, attempt + 1)
            else:
                logger.error("Max retries reached for title: %s", title)
                return None

    for _, (title_link, summary) in enumerate(
        zip(titles_and_links, summaries)
    ):
        response = fetch_summary(title_link, summary)
        if not response:
            continue

        result_dict[title_link] = response
        logger.info("Processed summary for: %s", title_link)

    return result_dict


def fetch_recent_articles(hours: int = 24) -> pd.DataFrame:
    daily_hours_summary = settings.daily_hours_summary
    daily_process_read = settings.daily_process_read
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(
        hours=daily_hours_summary if daily_hours_summary else hours
    )

    query = (
        db.session.query(FeedItem)
        .join(Feed, FeedItem.feed_id == Feed.id)
        .filter(Feed.daily_enabled == True)
        .outerjoin(ArticleLink, FeedItem.id == ArticleLink.original_article_id)
        .filter(ArticleLink.id == None)
        .filter(FeedItem.pub_date >= cutoff_date)
    )

    if not daily_process_read:
        query = query.filter(FeedItem.read == False)

    query = query.order_by(FeedItem.pub_date.desc())
    items = query.all()

    if not items:
        logger.info("No new items to process.")
        return pd.DataFrame()

    data = [
        {
            "id": item.id,
            "title": item.title,
            "summary": item.summary if item.summary else "",
            "link": item.link,
            "text": (item.title if item.title else "") * 5
            + " "
            + (item.summary if item.summary else ""),
        }
        for item in items
    ]

    return pd.DataFrame(data)


def summarize_clusters(
    clusters: list[list[int]], df: pd.DataFrame
) -> tuple[list[str], list[str]]:

    if len(clusters) == 0 or len(df) == 0:
        return [], []

    def merge_clusters(clusters: list[list[int]]) -> list[list[int]]:
        merged = []
        for cluster in clusters:
            found = False
            for mcluster in merged:
                if any(item in mcluster for item in cluster):
                    mcluster.update(cluster)
                    found = True
                    break
            if not found:
                merged.append(set(cluster))
        return [list(cluster) for cluster in merged]

    clusters = merge_clusters(clusters)
    used_indices = set()
    summaries = []
    titles_and_links = []

    def get_full_text_and_summary(idx: int) -> str:
        link = df.iloc[idx]["link"]
        try:
            _, text = get_text_from_url(link, processor="goose3")
            text = clean_text(text)
            summary = extract_summary(text, num_sentences=5)
            return summary
        except Exception as e:
            logger.error("Failed to fetch article: %s, Error: %s", link, e)
            return df.iloc[idx]["summary"]

    def check_similarity(cluster: list[int]) -> list[list[int]]:

        if settings.daily_title_provider == "openai":
            cluster_indices = [i for i, _ in enumerate(cluster)]
            logger.info(
                "Title provider is OpenAI, returning"
                "original cluster indices: %s",
                cluster_indices,
            )
            return [cluster_indices]
        api_key = settings.groq_api_key
        logger.info("Checking similarity for cluster: %s", cluster)
        titles_dict = {
            i: f"{df.iloc[idx]['title']} {get_full_text_and_summary(idx)}"
            for i, idx in enumerate(cluster)
        }
        logger.info("Sending for similarity check: %s", titles_dict)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = groq_compare_titles(
                    titles_dict, api_key, COMPARE_TITLES
                )
                if (
                    response is None
                    or not isinstance(response, tuple)
                    or not all(
                        isinstance(inner_list, list)
                        and all(isinstance(item, int) for item in inner_list)
                        for inner_list in response
                    )
                ):
                    logger.warning(
                        "Invalid response received, attempt %s", attempt + 1
                    )
                    if attempt == max_retries - 1:
                        logger.error(
                            "Max retries reached with invalid response"
                        )
                        return []
                else:
                    logger.info(
                        "Received valid similarity response: %s", response
                    )
                    return response
            except Exception as e:
                logger.error("Exception during similarity check: %s", e)
                if attempt == max_retries - 1:
                    return []

        return []

    if clusters:
        for cluster in clusters:
            if len(cluster) > 1:
                new_clusters = check_similarity(cluster)
                if not new_clusters:
                    continue

                for new_cluster in new_clusters:
                    title_link_list = []
                    cluster_text = []
                    for idx in new_cluster:
                        try:
                            idx = cluster[idx]
                            link = df.iloc[idx]["link"]
                            try:
                                _, text = get_text_from_url(
                                    link, processor="goose3"
                                )
                            except Exception as e:
                                logger.error(
                                    "Failed to fetch article: %s, Error: %s",
                                    link,
                                    e,
                                )
                                continue
                            text = clean_text(text)
                            title_link_list.append(
                                f"{df.iloc[idx]['title']} {link}"
                            )
                            cluster_text.append(text)
                            used_indices.add(idx)
                        except ValueError as e:
                            logger.error(
                                "Invalid index value: {idx}, Error: %s", e
                            )

                    if title_link_list:
                        combined_text = " ".join(cluster_text)
                        combined_summary = extract_summary(
                            combined_text, num_sentences=20
                        )
                        if combined_summary.strip():
                            titles_and_links.append("\n".join(title_link_list))
                            summaries.append(combined_summary)
                            logger.info(
                                "Summarized similar articles: %s",
                                title_link_list,
                            )
                        else:
                            logger.warning(
                                "Empty summary generated for: %s",
                                title_link_list,
                            )
    else:
        logger.info("No similar titles found.")

    for i in range(df.shape[0]):
        if i not in used_indices:
            title_link = f"{df.iloc[i]['title']} {df.iloc[i]['link']}"
            try:
                link = df.iloc[i]["link"]
                try:
                    _, text = get_text_from_url(link, processor="goose3")
                except Exception as e:
                    logger.error(
                        "Failed to fetch article: %s, Error: %s", link, e
                    )
                    continue
                text = clean_text(text)
                summary = extract_summary(text, num_sentences=20)
                if summary.strip():
                    summaries.append(summary)
                    logger.info(
                        "Processed article: %s %s",
                        df.iloc[i]["title"],
                        df.iloc[i]["link"],
                    )
                else:
                    summary = f"{df.iloc[i]['title']}\nSummary: No summary available.\nLink: {df.iloc[i]['link']}"
                    summaries.append(summary)
                    logger.warning(
                        "Empty summary generated for article: %s", title_link
                    )
            except Exception as e:
                summary = f"{df.iloc[i]['title']}\nSummary: Failed to fetch text.\nLink: {df.iloc[i]['link']}"
                summaries.append(summary)
                logger.error(
                    "Failed to process article: %s %s, Error: %s",
                    df.iloc[i]["title"],
                    df.iloc[i]["link"],
                    e,
                )

            titles_and_links.append(title_link)

    return summaries, titles_and_links


def save_summaries_to_db(processed_summaries: dict, df: pd.DataFrame) -> None:
    """
    Saves the processed summaries to the database.

    This function takes a dictionary of processed summaries and a Pandas
    DataFrame as input. It iterates over the summaries, checks if a summary is
    available for each article, and if so, saves the summary to the database.
    If a summary is not available, it skips the article. It also extracts the
    first image link from the summary and saves it to the database.

    Args:
        processed_summaries (dict): A dictionary of processed summaries where the
            keys are the title links and the values are the summaries.
        df (pd.DataFrame): A Pandas DataFrame containing the article data.

    Returns:
        None: This function does not return any value.

    Raises:
        None: This function does not raise any exceptions.

    Notes:
        This function assumes that the database is already set up and the
        necessary tables are created. It also assumes that the
        `SummarizedArticle` and `ArticleLink` models are defined and imported.
    """

    for title_link, summary in processed_summaries.items():
        if summary == "No summary available.":
            logger.info(
                "Skipping article with 'No summary available': %s", title_link
            )
            continue

        links = [link.split()[-1] for link in title_link.split("\n")]
        summarized_article = (
            db.session.query(SummarizedArticle)
            .filter_by(link=links[0])
            .first()
        )
        image_link = None
        for link in links:
            try:
                summary_text = df.loc[df["link"] == link, "summary"].values[0]
                image_link = extract_first_image_link_from_summary(
                    summary_text, link
                )
                if image_link:
                    break
            except Exception as e:
                logger.error(
                    "Failed to fetch image from summary: %s, Error: %s",
                    link,
                    e,
                )

        if not summarized_article:
            if settings.daily_translate:
                summary = translate_text_google(summary, settings.language)

            summarized_article = SummarizedArticle(
                summary=summary, link=links[0], image_link=image_link
            )
            db.session.add(summarized_article)
            db.session.commit()
            logger.info(
                "Created new summarized article with id: %s",
                summarized_article.id,
            )
        else:
            summarized_article.image_link = image_link
            db.session.commit()
            logger.info(
                "Using existing summarized article with id: %s",
                summarized_article.id,
            )

        logger.info("Title link split: %s", links)
        original_ids = [
            int(df.loc[df["link"] == link, "id"].values[0])
            for link in links
            if len(df.loc[df["link"] == link, "id"].values) > 0
        ]
        logger.info("Original IDs: %s", original_ids)

        for original_id in original_ids:
            logger.info(
                "Attempting to link original article %s with summarized article %s",
                original_id,
                summarized_article.id,
            )
            existing_link = (
                db.session.query(ArticleLink)
                .filter_by(
                    original_article_id=original_id,
                    summarized_article_id=summarized_article.id,
                )
                .first()
            )
            if not existing_link:
                article_link = ArticleLink(
                    original_article_id=original_id,
                    summarized_article_id=summarized_article.id,
                )
                db.session.add(article_link)
                db.session.commit()
                logger.info(
                    "Linked original article %s with summarized article %s",
                    original_id,
                    summarized_article.id,
                )
            else:
                logger.info(
                    "Link already exists for original"
                    "article %s with summarized article %s",
                    original_id,
                    summarized_article.id,
                )


def process_and_summarize_articles() -> None:
    """Main function for processing and summarizing articles.

    This function retrieves the most recent articles from the database,
    checks for similar titles using either the Groq or OpenAI API based on
    user settings, summarizes the articles into clusters, and finally saves
    the summarized results to the database. It follows these steps:

    1. Fetches recent articles that need to be processed.
    2. If no articles are found, the function ends early.
    3. Prepares a dictionary of article titles for similarity checking, limited
       to the first 1000 articles.
    4. Depending on the selected title provider
       (Groq or OpenAI), makes a request to check for similar titles.
    5. If no similar titles are found, initializes an empty cluster list.
    6. Otherwise, it proceeds with the received clusters.
    7. Summarizes the clusters of articles into concise summaries.
    8. Batches the summaries and sends them to the respective API for
       processing.
    9. Finally, saves the processed summaries back to the database.

    Returns:
        None: This function does not return any value.
    """
    groq_api_key = settings.groq_api_key
    openai_api_key = settings.openai_api_key
    title_provider = settings.daily_title_provider
    compare_titles = settings.daily_compare_titles

    df = fetch_recent_articles()
    if df.empty:
        return

    # Prepare titles for similarity checking if needed.
    if compare_titles:
        titles_dict = {i: title for i, title in enumerate(df["title"][:1000])}

        if title_provider == "groq":
            response = groq_compare_titles(
                titles_dict, groq_api_key, COMPARE_TITLES
            )
        elif title_provider == "openai":
            response = openai_compare_titles(
                titles_dict, openai_api_key, COMPARE_TITLES
            )

        if response is None:
            logger.info("No similar titles found.")
            clusters = []
        else:
            clusters = response
    else:
        clusters = []
        logger.info("Skipping title comparison based on settings.")

    summaries, titles_and_links = summarize_clusters(clusters, df)
    processed_summaries = summarize_batched_text(summaries, titles_and_links)
    save_summaries_to_db(processed_summaries, df)
