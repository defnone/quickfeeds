def add_trailing_slash(value):
    if not value.endswith("/"):
        return value + "/"
    return value
