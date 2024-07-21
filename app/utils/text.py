import re
from urllib.parse import urlparse
import ipaddress
import socket
import logging
import requests
from bs4 import BeautifulSoup
from goose3 import Goose
from goose3.network import NetworkError


def fetch_article(url):
    """
    Fetch the HTML content of the article at the given URL.

    Args:
        url (str): The URL of the article to fetch.

    Returns:
        str: The HTML content of the article.

    Raises:
        Exception: If the request to fetch the article fails or URL is not
        allowed.
    """
    # Validate the URL
    if not is_url_safe(url):
        logging.error("URL not safe: %s", url)
        raise ValueError("URL is not allowed.")

    try:
        # codeql [py/ssrf] Suppress warning: URL is properly validated
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Limit the size of the response to 5 MB
        if len(response.content) > 1024 * 1024 * 5:
            logging.error("Response content is too large: %s", url)
            raise ValueError("Response content is too large.")

        return response.text

    except requests.RequestException as e:
        logging.error("Failed to fetch article: %s", str(e))
        raise requests.RequestException(
            f"Failed to fetch article. Error: {str(e)}"
        )


def is_url_safe(url):
    """
    Checks if a given URL is safe to use.

    A URL is considered safe if: - It has a scheme of either "http" or "https".
    - The hostname is not private (e.g. 10.0.0.0/8, 172.16.0.0/12,
    192.168.0.0/16) and not localhost. - The hostname can be resolved to an IP
    address. - The URL does not exceed a certain length (e.g. 2048 characters).
    - It does not contain any potentially harmful characters such as '..',
    '\\', etc.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is safe, False otherwise.
    """
    try:
        parsed_url = urlparse(url)

        if len(url) > 2048:
            logging.error("URL exceeds maximum length")
            return False

        if parsed_url.scheme not in ("http", "https"):
            logging.error("Invalid scheme: %s", parsed_url.scheme)
            return False

        if not parsed_url.netloc:
            logging.error("Invalid netloc: %s", parsed_url.netloc)
            return False

        # Parse the netloc to get the hostname
        hostname = parsed_url.hostname
        if hostname is None:
            logging.error("Hostname could not be parsed")
            return False

        # Resolve the hostname to an IP address
        try:
            ip = socket.gethostbyname(hostname)
            ip_addr = ipaddress.ip_address(ip)
        except (socket.gaierror, ValueError):
            logging.error("Failed to resolve hostname: %s", hostname)
            return False

        # Disallow private IP addresses and localhost
        if ip_addr.is_private or ip_addr.is_loopback:
            logging.error(
                "Private IP or loopback address detected: %s", ip_addr
            )
            return False

        # Check for harmful characters in the URL
        for harmful_char in "..", "\\":
            if harmful_char in url:
                logging.error(
                    "Harmful character detected in URL: %s", harmful_char
                )
                return False

        return True
    except ValueError:
        logging.error("ValueError occurred, URL is not safe")
        return False


def parse_article(html_content):
    """
    Extracts the title and text from an HTML article content.

    Args:
        html_content (str): The HTML content of the article to parse.

    Returns:
        tuple: A tuple containing the title and text of the article, truncated
        to 5900 characters.

    Notes:
        This function uses the BeautifulSoup library to parse the HTML content.
        The title is extracted from the first `<h1>` tag, and the text is
        extracted from all `<p>` tags.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    title = soup.find("h1").get_text()
    paragraphs = soup.find_all("p")
    text = " ".join([p.get_text() for p in paragraphs])
    return title, text[:5900]


def parse_article_as_goose3(url):
    """
    Extracts the title and cleaned text from an article
    URL using Goose3 library.

    Args:
        url (str): The URL of the article to extract.

    Returns:
        tuple: A tuple containing the article title and cleaned text,
        or (None, None) if the URL is not safe.

    Notes:
        This function uses the Goose3 library to extract the article content.
        The `is_url_safe` function is used to check
        if the URL is safe to extract.
    """
    g = Goose()
    if is_url_safe(url):
        article = g.extract(url=url)
    else:
        return None, None
    return article.title, article.cleaned_text


def get_image_from_url(url):
    """
    Extracts the image URL from an article URL using Goose3 library.

    Args:
        url (str): The URL of the article to extract the image from.

    Returns:
        str: The URL of the extracted image, or None if the URL is
            not safe or an error occurs.

    Notes:
        This function uses the Goose3 library to extract the article content.
        The `is_url_safe` function is used to check if the
        URL is safe to extract.
        If a NetworkError or any other exception occurs during
        the extraction process, an error message is logged and None
        is returned.
    """
    g = Goose()
    try:
        if is_url_safe(url):
            article = g.extract(url=url)
            image_url = article.infos["opengraph"]["image"]
        else:
            image_url = None
    except NetworkError as e:
        logging.error("Network error occurred while fetching image: %s", e)
        image_url = None
    except Exception as e:
        logging.error("Unexepted error occurred while fetching image: %s", e)
        image_url = None
    return image_url


def get_text_from_url(url, processor="bs4"):
    """
    Extracts the title and text from an article at the given URL.

    Args:
        url (str): The URL of the article to extract.
        processor (str, optional): The processor to use for extraction.
            Defaults to "bs4" for BeautifulSoup. Can also be "goose3" for
            Goose3.

    Returns:
        tuple: A tuple containing the title and text of the article.

    Notes:
        If processor is "bs4", the function uses BeautifulSoup to parse the
        HTML content of the article. If processor is "goose3", the function
        uses Goose3 to extract the article content.
    """
    if processor == "bs4":
        html_content = fetch_article(url)
        return parse_article(html_content)
    elif processor == "goose3":
        return parse_article_as_goose3(url)


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
