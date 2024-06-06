from groq import Groq
import logging


def groq_request(article_tuple, api_key, promt="Summarize the text"):
    title, text = article_tuple
    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": promt},
            {"role": "user", "content": text},
        ],
        temperature=0.39,
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    response = completion.choices[0].message.content
    return response


def check_groq_api(text, api_key):
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
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
        logging.error(f"Error checking GROQ API: {e}", exc_info=True)
        return False
