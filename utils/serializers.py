from flask import current_app

from models.link_model import LinkModel
from utils.formatting import domain


def serialize_link(link):
    base = current_app.config["BASE_URL"]
    expires_at = link.get("expires_at")
    return {
        "id": str(link["_id"]),
        "short_code": link["short_code"],
        "short_url": f"{base}/{link['short_code']}",
        "original_url": link["original_url"],
        "title": link.get("title") or "",
        "display_title": link.get("title") or domain(link["original_url"]),
        "domain": domain(link["original_url"]),
        "tags": link.get("tags", []),
        "clicks": link.get("clicks", 0),
        "is_active": link.get("is_active", True),
        "on_profile": link.get("on_profile", False),
        "expired": LinkModel.is_expired(link),
        "expires_on": expires_at.strftime("%Y-%m-%d") if expires_at else "",
        "created_at": link["created_at"].isoformat() if link.get("created_at") else None,
        "qr": {"fg": link.get("qr", {}).get("fg") or "#101010", "bg": link.get("qr", {}).get("bg") or "#FFFFFF"},
    }
