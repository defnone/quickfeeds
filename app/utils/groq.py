import re
from groq import Groq
import logging


def groq_request(
    article_tuple,
    api_key,
    promt="Summarize the text",
    both=False,
    model="70b",
    tokens=1024,
):
    title, text = article_tuple
    if both:
        text = f"{title}\n\n{text}"

    if model == "70b":
        model = "llama-3.3-70b-versatile"
    elif model == "8b":
        model = "llama-3.1-8b-instant"

    client = Groq(api_key=api_key, timeout=10.0)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": promt},
            {"role": "user", "content": text},
        ],
        temperature=0.39,
        max_tokens=tokens,
        top_p=1,
        stream=False,
        stop=None,
    )

    response = completion.choices[0].message.content
    logging.debug('Groq response: "%s"', response)
    return response


def groq_request_8b(
    article_tuple,
    api_key,
    promt="Summarize the text",
    both=False,
):
    title, text = article_tuple
    if both:
        text = f"{title}\n\n{text}"

    text = f"{text}\n\n{promt}"

    client = Groq(api_key=api_key, timeout=10.0)
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": text},
        ],
        temperature=0.70,
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    response = completion.choices[0].message.content
    logging.debug('Groq response: "%s"', response)
    return response


def groq_compare_titles(text, api_key, prompt="Summarize the text"):
    text = str(text)
    client = Groq(api_key=api_key, timeout=10.0)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.30,
        stream=False,
        stop=None,
    )

    try:
        response = completion.choices[0].message.content
    except Exception as e:
        logging.error(
            "Error in groq_request_list,"
            "return None for skipping. Error: %s",
            e,
        )

    # print("Groq title response", response)

    if response in [None, "(None)", "None"]:
        return None

    if not response or (response and "[" not in response):
        return {"error": "Empty or format error response from API"}

    try:
        lists = re.findall(r"\[([^\[\]]+)\]", response)
        parsed_lists = [list(map(int, lst.split(","))) for lst in lists]
        return tuple(parsed_lists)
    except Exception as e:
        return {"error": "Failed to parse the response: {e}".format(e=e)}


def check_groq_api(api_key):
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Return only pong."},
                {"role": "user", "content": "ping"},
            ],
            temperature=0.39,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        groq_response = str(completion.choices[0].message.content).lower()

        if "pong" in groq_response:
            return True
        return False
    except Exception as e:
        logging.error("Error checking GROQ API: %s", e, exc_info=True)
        return False
