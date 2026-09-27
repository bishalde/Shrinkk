"""Validation and orchestration for creating and editing links (shared by forms and JSON API)."""
from datetime import datetime, time, timedelta, timezone
from urllib.parse import urlparse

from flask import current_app

from extensions import repos
from services.shortener import generate_unique_code
from utils.validators import is_hex_color, is_valid_alias, is_valid_url

MAX_TAGS = 10
MAX_TAG_LEN = 24
MAX_TITLE_LEN = 100


class LinkError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def normalize_url(raw):
    url = (raw or "").strip()
    if url and "://" not in url:
        url = f"https://{url}"
    if not is_valid_url(url):
        raise LinkError("Enter a valid URL, like https://example.com.")
    own_host = urlparse(current_app.config["BASE_URL"]).netloc
    if urlparse(url).netloc.lower() == own_host.lower():
        raise LinkError("That's already a Shrinkk link.")
    return url


def parse_tags(raw):
    if isinstance(raw, str):
        raw = raw.split(",")
    tags = []
    for tag in raw or []:
        tag = str(tag).strip().lower()[:MAX_TAG_LEN]
        if tag and tag not in tags:
            tags.append(tag)
    return tags[:MAX_TAGS]


def parse_expiry(data):
    """`expires_on` (YYYY-MM-DD, end of that day UTC) or legacy `expires_in` (hours)."""
    expires_on = (data.get("expires_on") or "").strip()
    if expires_on:
        try:
            day = datetime.strptime(expires_on, "%Y-%m-%d").date()
        except ValueError as exc:
            raise LinkError("Expiry date must be a valid date.") from exc
        expires_at = datetime.combine(day, time(23, 59, 59), tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise LinkError("Expiry date must be in the future.")
        return expires_at
    expires_in = data.get("expires_in")
    if expires_in:
        try:
            hours = int(expires_in)
        except (TypeError, ValueError) as exc:
            raise LinkError("expires_in must be a number of hours.") from exc
        if hours > 0:
            return datetime.now(timezone.utc) + timedelta(hours=hours)
    return None


def _check_alias(alias, exclude_link_id=None):
    if not is_valid_alias(alias):
        raise LinkError("Aliases are 3–30 letters, numbers, hyphens or underscores, and can't be a reserved word.")
    if repos().links.short_code_taken(alias, exclude_link_id):
        raise LinkError("That alias is already taken.", 409)


def _truthy(value):
    return value in (True, "true", "on", "1", 1)


def create_link(user_id, data):
    links = repos().links
    original_url = normalize_url(data.get("original_url"))
    alias = (data.get("custom_alias") or "").strip() or None
    if alias:
        _check_alias(alias)
    short_code = alias or generate_unique_code(links)
    link_id = links.create_link(
        user_id=user_id,
        original_url=original_url,
        short_code=short_code,
        custom_alias=alias,
        expires_at=parse_expiry(data),
        title=(data.get("title") or "").strip()[:MAX_TITLE_LEN],
        tags=parse_tags(data.get("tags")),
        on_profile=_truthy(data.get("on_profile")),
    )
    return link_id, short_code


def update_link(link, data):
    """Apply edits from the link modal. Only fields present in `data` are changed."""
    updates = {}
    if "original_url" in data:
        updates["original_url"] = normalize_url(data["original_url"])
    if "custom_alias" in data:
        alias = (data.get("custom_alias") or "").strip()
        if alias and alias != link["short_code"]:
            _check_alias(alias, exclude_link_id=link["_id"])
            updates["short_code"] = alias
            updates["custom_alias"] = alias
    if "title" in data:
        updates["title"] = (data.get("title") or "").strip()[:MAX_TITLE_LEN]
    if "tags" in data:
        updates["tags"] = parse_tags(data["tags"])
    if "expires_on" in data or "expires_in" in data:
        updates["expires_at"] = parse_expiry(data)
    for flag in ("on_profile", "is_active"):
        if flag in data:
            updates[flag] = _truthy(data[flag])
    qr = {k: data[k].upper() for k in ("qr_fg", "qr_bg") if is_hex_color(data.get(k))}
    if qr:
        updates["qr"] = {"fg": qr.get("qr_fg", link.get("qr", {}).get("fg")),
                         "bg": qr.get("qr_bg", link.get("qr", {}).get("bg"))}
    if updates:
        repos().links.update_link(str(link["_id"]), str(link["user_id"]), updates)
    return updates


def delete_links(user_id, link_ids):
    deleted = repos().links.delete_many(link_ids, user_id)
    repos().events.delete_for_links(deleted)
    return len(deleted)
