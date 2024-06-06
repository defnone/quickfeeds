import pytest
from app.utils.translate import (
    translate_text_google,
)


def test_translate_text_google_to_russian():
    """
    Test case for the function translate_text_google when translating English
    text to Russian.

    This test checks if the function is able to translate a given English text
    to Russian. It asserts that the translated text is not None, is a string,
    and has a length greater than 0.
    """
    text = "Hello, world!"
    translated_text = translate_text_google(text, "Russian")
    assert translated_text is not None
    assert isinstance(translated_text, str)
    assert len(translated_text) > 0


def test_translate_text_google_invalid_language():
    """
    Test case for the function translate_text_google when an invalid language
    is provided.

    This test checks if the function raises an Exception when an invalid
    language is provided for translation. It uses pytest's raises context
    manager to catch the exception.
    """
    text = "Hello, world!"
    with pytest.raises(Exception):
        translate_text_google(text, "InvalidLanguage")


def test_translate_text_google_empty_text():
    """
    Test case for the function translate_text_google when an empty text is
    provided.

    This test checks if the function raises an Exception when an empty string
    is provided for translation. It uses pytest's raises context manager to
    catch the exception.
    """
    with pytest.raises(Exception):
        translate_text_google("", "Russian")
