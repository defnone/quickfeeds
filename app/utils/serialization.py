"""
This module contains a function for serializing an item object into a
dictionary, including additional information like feed title and publication
date.
"""

import pytz


def serialize_item(item, user_timezone):
    """
    Serializes an item object into a dictionary, including additional
    information like feed title and publication date.

    Args:
        item (Item): The item object to be serialized. user_timezone
        (timezone): The timezone to be used for converting the publication
        date.

    Returns:
        dict: A dictionary containing the serialized item data.
    """
    item_dict = item.to_dict()
    item_dict["feed_title"] = item.feed.title
    if item.pub_date:
        item.pub_date = item.pub_date.replace(tzinfo=pytz.utc).astimezone(
            user_timezone
        )
        item_dict["pub_date"] = item.pub_date.isoformat()

    return item_dict
