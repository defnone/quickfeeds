"""
This module provides functions for fetching and parsing articles from the web.
It includes utilities for URL validation, HTTP requests, and HTML parsing.
"""

import re
from urllib.parse import urlparse
import ipaddress
import socket
import logging
import requests
from bs4 import BeautifulSoup


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
    Fetch the HTML content of an article at the given URL and parse it to
    extract the title and text.

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
