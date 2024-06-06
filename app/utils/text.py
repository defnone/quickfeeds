import requests
from bs4 import BeautifulSoup
import re


def fetch_article(url):
    """
    Fetch the HTML content of the article at the given URL.

    Args:
        url (str): The URL of the article to fetch.

    Returns:
        str: The HTML content of the article.

    Raises:
        Exception: If the request to fetch the article fails.
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(
            f"Failed to fetch article. Status code: {response.status_code}"
        )


def parse_article(html_content):
    """
    Parse the HTML content of an article and extract the title and text.

    Args:
        html_content (str): The HTML content of the article.

    Returns:
        tuple: The title and text of the article.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    title = soup.find("h1").get_text()
    paragraphs = soup.find_all("p")
    text = " ".join([p.get_text() for p in paragraphs])
    return title, text[:5900]


def get_text_from_url(url):
    """
    Fetch the HTML content of an article at the given URL and parse it to extract the title and text.

    Args:
        url (str): The URL of the article to fetch and parse.

    Returns:
        tuple: The title and text of the article.
    """
    html_content = fetch_article(url)
    return parse_article(html_content)


def text_to_html_list(text):
    """
    Convert a text with list items into an HTML list.

    Args:
        text (str): The text to convert.

    Returns:
        str: The HTML list.
    """
    lines = text.strip().split("\n")
    html_lines = ["<ul>"]
    list_item_regex = r"^[\s]*(\*|\+|•|\d+\.)\s*(.*)$"

    for line in lines:
        match = re.match(list_item_regex, line)
        if not match:
            continue

        clean_line = match.group(2)
        html_lines.append(f"  <li>{clean_line}</li>")

    html_lines.append("</ul>")
    html = "\n".join(html_lines) + "\n"
    return html
