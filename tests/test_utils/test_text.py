import unittest
import requests
from unittest.mock import patch, Mock
from app.utils.text import (
    fetch_article,
    parse_article,
    get_text_from_url,
    text_to_html_list,
    is_url_safe,
)


class TestArticleUtils(unittest.TestCase):
    """
    This class contains unit tests for the article utilities.
    """

    @patch("app.utils.text.requests.get")
    def test_fetch_article_success(self, mock_get):
        """
        Test the fetch_article function with a successful response.
        """
        # Mock the response of requests.get
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><h1>Test Article</h1></html>"
        mock_response.content = mock_response.text.encode(
            "utf-8"
        )  # Mock the content attribute
        mock_get.return_value = mock_response

        url = "http://example.com/article"
        result = fetch_article(url)
        self.assertEqual(result, "<html><h1>Test Article</h1></html>")

    @patch("app.utils.text.requests.get")
    def test_fetch_article_failure(self, mock_get):
        """
        Test the fetch_article function with a failure response.
        """
        # Mock the response of requests.get
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.RequestException(
            "404 Client Error: Not Found for url"
        )
        mock_get.return_value = mock_response

        url = "http://example.com/article"
        with self.assertRaises(requests.RequestException) as context:
            fetch_article(url)
        self.assertIn(
            "Failed to fetch article. Error: 404 Client Error: Not Found for url",
            str(context.exception),
        )

    def test_parse_article(self):
        """
        Test the parse_article function.
        """
        html_content = "<html><h1>Test Title</h1><p>Paragraph 1.</p><p>Paragraph 2.</p></html>"
        title, text = parse_article(html_content)
        self.assertEqual(title, "Test Title")
        self.assertEqual(text, "Paragraph 1. Paragraph 2.")

    @patch("app.utils.text.fetch_article")
    def test_get_text_from_url(self, mock_fetch_article):
        """
        Test the get_text_from_url function.
        """
        mock_fetch_article.return_value = """
        <html><h1>Test Title</h1><p>Paragraph 1.</p><p>Paragraph 2.</p></html>
        """

        url = "http://example.com/article"
        title, text = get_text_from_url(url)
        self.assertEqual(title, "Test Title")
        self.assertEqual(text, "Paragraph 1. Paragraph 2.")

    def test_text_to_html_list(self):
        """
        Test the text_to_html_list function.
        """
        text = """
        * Item 1
        * Item 2
        * Item 3
        """
        expected_html = "<ul>\n  <li>Item 1</li>\n  <li>Item 2</li>\n  <li>Item 3</li>\n</ul>\n"
        result = text_to_html_list(text)
        self.assertEqual(result, expected_html)

    def test_is_url_safe_valid_url(self):
        """
        Test the is_url_safe function with a valid URL.
        """
        url = "http://example.com"
        self.assertTrue(is_url_safe(url))

    def test_is_url_safe_invalid_scheme(self):
        """
        Test the is_url_safe function with an invalid scheme.
        """
        url = "ftp://example.com"
        self.assertFalse(is_url_safe(url))

    def test_is_url_safe_private_ip(self):
        """
        Test the is_url_safe function with a private IP address.
        """
        url = "http://192.168.0.1"
        self.assertFalse(is_url_safe(url))

    def test_is_url_safe_loopback(self):
        """
        Test the is_url_safe function with a loopback address.
        """
        url = "http://localhost"
        self.assertFalse(is_url_safe(url))

    def test_is_url_safe_invalid_hostname(self):
        """
        Test the is_url_safe function with an invalid hostname.
        """
        url = "http://invalid.hostname"
        self.assertFalse(is_url_safe(url))


if __name__ == "__main__":
    unittest.main()
