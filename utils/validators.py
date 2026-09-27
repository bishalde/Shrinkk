import re
from urllib.parse import urlparse


def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def is_valid_alias(alias):
    pattern = r"^[a-zA-Z0-9_-]{3,30}$"
    return bool(re.match(pattern, alias))
