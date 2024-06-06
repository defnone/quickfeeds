import logging
import requests
from bs4 import BeautifulSoup
import urllib.parse


def translate_text_google(text, target_language="Russian"):
    if not text:
        raise ValueError("Text for translation cannot be empty.")

    language_codes = {
        "Russian": "ru",
        "English": "en",
        "German": "de",
        "French": "fr",
        "Spanish": "es",
        "Italian": "it",
        "Chinese": "zh-CN",
        "Japanese": "ja",
        "Korean": "ko",
    }

    target_language_code = language_codes.get(target_language)
    if not target_language_code:
        raise ValueError(f"Invalid target language: {target_language}")

    base_url = "https://translate.google.com/m"
    params = {"sl": "auto", "tl": target_language_code, "q": text}
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Failed to translate text. Status code: {response.status_code}"
        )

    soup = BeautifulSoup(response.text, "html.parser")
    translated_text = soup.find("div", {"class": "result-container"}).text
    logging.debug(f"Translated text: {translated_text}")
    return translated_text
