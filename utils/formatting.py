from datetime import datetime, timezone
from urllib.parse import urlparse


def compact(n):
    n = n or 0
    for divisor, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "k")):
        if n >= divisor:
            value = n / divisor
            return f"{value:.1f}".rstrip("0").rstrip(".") + suffix
    return str(n)


def domain(url):
    host = urlparse(url or "").netloc
    return host[4:] if host.startswith("www.") else host


def timeago(dt):
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    seconds = int((datetime.now(timezone.utc) - dt).total_seconds())
    for unit, size in (("y", 31_536_000), ("mo", 2_592_000), ("d", 86_400), ("h", 3_600), ("m", 60)):
        if seconds >= size:
            return f"{seconds // size}{unit} ago"
    return "just now"


def datefmt(dt, fmt="%b %-d, %Y"):
    return dt.strftime(fmt) if dt else ""


def flag(country_code):
    """🇺🇸-style flag emoji for an ISO alpha-2 code."""
    if not country_code or len(country_code) != 2 or not country_code.isalpha():
        return "🌐"
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in country_code.upper())


def register_filters(app):
    app.jinja_env.filters.update(
        compact=compact, domain=domain, timeago=timeago, datefmt=datefmt, flag=flag,
    )
