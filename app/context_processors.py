from .utils.version import get_version


def inject_version():
    return {"version": get_version()}
