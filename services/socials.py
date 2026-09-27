"""Social profiles a user can show on their bio page."""
import re

from utils.validators import is_valid_email, is_valid_url

# key -> label, sprite icon, URL template for a bare handle
NETWORKS = {
    "instagram": {"label": "Instagram", "icon": "brand-instagram", "template": "https://instagram.com/{}"},
    "x": {"label": "X", "icon": "brand-x", "template": "https://x.com/{}"},
    "tiktok": {"label": "TikTok", "icon": "brand-tiktok", "template": "https://tiktok.com/@{}"},
    "youtube": {"label": "YouTube", "icon": "brand-youtube", "template": "https://youtube.com/@{}"},
    "linkedin": {"label": "LinkedIn", "icon": "brand-linkedin", "template": "https://linkedin.com/in/{}"},
    "github": {"label": "GitHub", "icon": "brand-github", "template": "https://github.com/{}"},
    "email": {"label": "Email", "icon": "mail", "template": "mailto:{}"},
    "website": {"label": "Website", "icon": "globe", "template": "{}"},
}

HANDLE_RE = re.compile(r"^@?([A-Za-z0-9_.\-]{1,64})$")


def to_url(network, value):
    """Normalize a handle or URL for `network`. Returns None if it isn't usable."""
    value = (value or "").strip()
    if not value:
        return None
    if network == "email":
        return f"mailto:{value}" if is_valid_email(value) else None
    if is_valid_url(value):
        return value
    if network == "website":
        return f"https://{value}" if is_valid_url(f"https://{value}") and "." in value else None
    match = HANDLE_RE.match(value)
    return NETWORKS[network]["template"].format(match.group(1)) if match else None


def clean(raw):
    """Keep the raw values the user typed (for re-editing) when they normalize to a URL."""
    raw = raw or {}
    out, errors = {}, {}
    for key in NETWORKS:
        value = (raw.get(key) or "").strip()
        if not value:
            continue
        if to_url(key, value):
            out[key] = value
        else:
            errors[key] = f"That doesn't look like a valid {NETWORKS[key]['label']} handle or URL."
    return out, errors


def for_display(socials):
    return [
        {"key": key, **NETWORKS[key], "url": to_url(key, value)}
        for key, value in (socials or {}).items()
        if key in NETWORKS and to_url(key, value)
    ]
