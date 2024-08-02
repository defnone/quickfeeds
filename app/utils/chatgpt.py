import logging
import re
from openai import OpenAI


def openai_compare_titles(titles, api_key, promt):
    """
    Sends a request to the OpenAI API to get a list based on provided titles.

    This function constructs a message to be sent to the OpenAI
    API given a list of titles, an API key for authentication,
    and a prompt message. The titles are sanitized to remove
    specific characters before being sent.

    Parameters:
    titles (str | list): The input titles to be processed.
        If a list is provided, it is joined into a single string.
    api_key (str): The API key used to authenticate with the OpenAI
        service.
    promt (str): The prompt message that instructs the API on the
        expected response format.

    Returns:
    tuple | dict | None:
        If the response is valid and contains lists, returns a tuple
        of lists parsed from the response. If the response is empty
        or improperly formatted, it returns a dictionary with an
        error message. If an exception occurs, it returns a
        dictionary with the error details, or None if the response
        is interpreted as a non-value.
    """

    titles = str(titles)
    client = OpenAI(api_key=api_key, timeout=10.0, max_retries=3)
    trans = str.maketrans("", "", "{}")
    titles = titles.translate(trans)
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": promt,
                },
                {
                    "role": "user",
                    "content": titles,
                },
            ],
            stream=False,
            temperature=0.5,
        )

        response = completion.choices[0].message.content

    except Exception as e:
        logging.warning("OpenAIError: %s", str(e))
        return {"OpenAI error": str(e)}

    if response in [None, "(None)", "None"]:
        return None

    if not response or (response and "[" not in response):
        return {"error": "Empty or format error response from API"}

    logging.debug("OpenAI response: %s", response)
    try:
        lists = re.findall(r"\[([^\[\]]+)\]", response)
        parsed_lists = [list(map(int, lst.split(","))) for lst in lists]
        return tuple(parsed_lists)
    except Exception as e:
        logging.warning(
            "Failed to parse the response and convert to tuple: %s", e
        )
        raise ValueError("Empty or format error response from API %e", e)
