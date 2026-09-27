"""Everything we derive from an incoming request: client IP, geo, device and referrer."""
from urllib.parse import unquote, urlparse

from flask import request
from user_agents import parse as parse_ua

SOURCES = ("direct", "bio", "qr")


def client_ip():
    """Real client IP behind Vercel's proxy (first X-Forwarded-For hop)."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.headers.get("X-Real-Ip") or request.remote_addr or "unknown"


def geo():
    """Country (ISO-3166 alpha-2) and city from Vercel's edge headers; None when absent."""
    country = request.headers.get("X-Vercel-IP-Country") or None
    city = request.headers.get("X-Vercel-IP-City")
    return {
        "country": country.upper() if country else None,
        "city": unquote(city) if city else None,
    }


def referrer_domain():
    ref = request.referrer
    if not ref:
        return None
    host = urlparse(ref).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def visitor():
    """Visitor details for analytics. `is_bot` visitors are redirected but not counted."""
    ua = parse_ua(request.headers.get("User-Agent", ""))
    if ua.is_mobile:
        device = "Mobile"
    elif ua.is_tablet:
        device = "Tablet"
    else:
        device = "Desktop"

    source = request.args.get("src", "direct")
    if source not in SOURCES:
        source = "direct"

    return {
        **geo(),
        "device": device,
        "browser": ua.browser.family or None,
        "os": ua.os.family or None,
        "referrer": referrer_domain(),
        "source": source,
        "is_bot": ua.is_bot,
    }
