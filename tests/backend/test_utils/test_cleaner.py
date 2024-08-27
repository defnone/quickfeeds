import pytest
from bs4 import BeautifulSoup
from app.utils.cleaner import clean_summary


def setup_function():
    pass


def test_remove_comments():
    summary = "<!-- This is a comment -->"
    cleaned_summary = clean_summary(summary)
    assert "<!-- This is a comment -->" not in cleaned_summary


def test_remove_unallowed_tags():
    summary = "<script>alert('Hello');</script>"
    cleaned_summary = clean_summary(summary)
    assert "<script>" not in cleaned_summary


def test_remove_unallowed_attributes():
    summary = '<img src="image.jpg" onclick="alert(\'Hello\');">'
    cleaned_summary = clean_summary(summary)
    assert "onclick=\"alert('Hello');\"" not in cleaned_summary


def test_remove_empty_links():
    summary = '<a href="#"></a>'
    cleaned_summary = clean_summary(summary)
    assert '<a href="#"></a>' not in cleaned_summary


def test_remove_button_tags():
    summary = "<button>Click me</button>"
    cleaned_summary = clean_summary(summary)
    assert "<button>" not in cleaned_summary


def test_remove_div_and_svg_tags():
    summary = "<div>Some text</div><svg>Some SVG</svg>"
    cleaned_summary = clean_summary(summary)
    assert "<div>" not in cleaned_summary
    assert "<svg>" not in cleaned_summary
    assert "Some text" in cleaned_summary
    assert "Some SVG" in cleaned_summary


def test_handle_iframes():
    summary = '<iframe src="video.mp4" width="640px" height="480px"></iframe>'
    cleaned_summary = clean_summary(summary)
    soup = BeautifulSoup(cleaned_summary, "html.parser")
    iframe = soup.find("iframe")
    assert iframe["width"] == "100%"
    assert "height" in iframe.attrs
    assert iframe["height"] == "360px"


if __name__ == "__main__":
    test_remove_comments()
    test_remove_unallowed_tags()
    test_remove_unallowed_attributes()
    test_remove_empty_links()
    test_remove_button_tags()
    test_remove_div_and_svg_tags()
    test_handle_iframes()
    print("All tests passed.")
