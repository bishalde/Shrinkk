import re
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
ALIAS_RE = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")
USERNAME_RE = re.compile(r"^[a-z0-9_.]{3,30}$")
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

# Top-level paths owned by the app. Neither aliases nor usernames may use them.
RESERVED = frozenset({
    "about", "account", "admin", "api", "app", "assets", "auth", "blog", "contact",
    "dashboard", "docs", "favicon.ico", "help", "home", "legal", "login", "logout",
    "media", "onboarding", "pricing", "privacy", "qr", "robots.txt", "root", "settings",
    "shrinkk", "signup", "static", "support", "terms", "www",
})


def is_valid_email(email):
    return bool(EMAIL_RE.match(email or ""))


def is_valid_url(url):
    if not url or any(c.isspace() for c in url):
        return False
    try:
        result = urlparse(url)
        host = result.hostname or ""
    except (ValueError, AttributeError):
        return False
    return result.scheme in ("http", "https") and ("." in host or host == "localhost")


def is_valid_alias(alias):
    return bool(ALIAS_RE.match(alias or "")) and alias.lower() not in RESERVED


def normalize_username(username):
    return (username or "").strip().lstrip("@").lower()


def username_error(username):
    """Why `username` (already normalized) is unusable, or None if the format is fine."""
    if not USERNAME_RE.match(username):
        return "Use 3–30 lowercase letters, numbers, dots or underscores."
    if username.startswith(".") or username.endswith(".") or ".." in username:
        return "Dots can't be at the start, end, or next to each other."
    if username in RESERVED:
        return "That username is reserved."
    return None


def is_hex_color(value):
    return bool(HEX_COLOR_RE.match(value or ""))


def is_safe_next(target):
    """Only allow same-site relative paths as post-login redirects."""
    if not target or not target.startswith("/") or target.startswith("//"):
        return False
    return not urlparse(target).netloc and "\\" not in target
