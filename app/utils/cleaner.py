from bs4 import BeautifulSoup, Comment
import logging

# Global constants for allowed tags and attributes
ALLOWED_TAGS = [
    "iframe",
    "img",
    "p",
    "br",
    "b",
    "i",
    "u",
    "a",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "blockquote",
    "table",
    "tr",
    "td",
    "th",
    "figure",
    "figcaption",
    "mark",
    "audio",
    "video",
    "source",
    "del",
    "ins",
    "sub",
    "sup",
    "code",
    "pre",
    "enclosure",
]

ALLOWED_ATTRIBUTES = {
    "img": ["src", "alt", "title"],
    "iframe": [
        "src",
        "title",
        "width",
        "height",
        "frameborder",
        "allowfullscreen",
    ],
    "a": ["href", "title"],
    "audio": ["controls", "src"],
    "video": ["controls", "src", "width", "height"],
    "source": ["src", "type"],
    "image": ["src", "alt", "title"],
    "enclosure": [
        "length",
        "type",
        "url",
    ],
}


def clean_summary(summary):
    """
    This function cleans and formats the summary text of channel items. It
    removes all HTML tags that are not in the allowed list, removes all tag
    attributes that are not in the allowed list for each tag, removes empty
    links and buttons, handles iframe tags.
    """
    soup = BeautifulSoup(summary, "html.parser")

    # Remove all comments
    comments = soup.findAll(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment.extract()

    # Remove all tags except allowed ones, preserving the text inside them
    for tag in soup.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()

    # Remove unwanted attributes from allowed tags
    for tag in soup.find_all(True):
        allowed_attrs = ALLOWED_ATTRIBUTES.get(tag.name, [])
        attrs = tag.attrs.copy()
        for attr in attrs:
            if attr not in allowed_attrs:
                del tag.attrs[attr]

    # Remove empty links
    for a in soup.find_all("a"):
        if not a.get_text(strip=True):
            a.decompose()

    # Remove button tags
    for button in soup.find_all("button"):
        button.decompose()

    # Remove all div and svg tags, leaving the text inside them
    for tag_name in ["div", "svg"]:
        for tag in soup.find_all(tag_name):
            tag.unwrap()

    # Handle iframes
    iframes = soup.find_all("iframe")
    aspect_ratio = 16 / 9
    for iframe in iframes:
        if "width" in iframe.attrs:
            try:
                original_width = int(
                    iframe["width"].strip("px").replace("%", "")
                )
                calculated_height = int(original_width / aspect_ratio)
                iframe["height"] = str(calculated_height) + "px"
            except ValueError as e:
                logging.error(f"Error parsing iframe width: {e}")
                iframe["height"] = "auto"
        iframe["width"] = "100%"

    # Convert back to string
    cleaned_summary = str(soup)

    return cleaned_summary
