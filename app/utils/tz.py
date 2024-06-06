from dateutil.tz import gettz


def tzinfos(tzname, tzoffset=None):
    timezones = {
        "PST": "US/Pacific",
        "PDT": "US/Pacific",
        "MST": "US/Mountain",
        "MDT": "US/Mountain",
        "CST": "US/Central",
        "CDT": "US/Central",
        "EST": "US/Eastern",
        "EDT": "US/Eastern",
        "UTC": "UTC",
        "GMT": "Etc/GMT",
        "BST": "Europe/London",
        "CET": "Europe/Paris",
        "CEST": "Europe/Paris",
        "EET": "Europe/Athens",
        "EEST": "Europe/Athens",
        "IST": "Asia/Kolkata",
        "CCT": "Asia/Shanghai",
        "JST": "Asia/Tokyo",
        "AEST": "Australia/Sydney",
        "AEDT": "Australia/Sydney",
        "ACST": "Australia/Adelaide",
        "ACDT": "Australia/Adelaide",
        "AWST": "Australia/Perth",
    }
    return gettz(timezones.get(tzname))
