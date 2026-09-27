import time

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from extensions import limiter, repos
from services.link_service import LinkError, create_link, normalize_url
from utils.helpers import current_user

pages_bp = Blueprint("pages", __name__)

_stats_cache = {"at": 0.0, "value": None}


def site_stats():
    """Real platform totals for the landing page, cached per function instance."""
    ttl = current_app.config["STATS_CACHE_SECONDS"]
    if _stats_cache["value"] is None or time.time() - _stats_cache["at"] > ttl:
        try:
            r = repos()
            _stats_cache["value"] = {
                "users": r.users.count(),
                "links": r.links.count(),
                "clicks": r.links.total_clicks(),
            }
        except Exception:  # landing page must render even if the DB is unreachable
            current_app.logger.exception("Could not load landing stats")
            _stats_cache["value"] = {"users": 0, "links": 0, "clicks": 0}
        _stats_cache["at"] = time.time()
    return _stats_cache["value"]


@pages_bp.route("/")
def landing():
    return render_template("landing.html", stats=site_stats())


@pages_bp.route("/shorten", methods=["POST"])
@limiter.limit("20 per minute")
def shorten():
    """Landing-page shortener. Logged-out visitors keep their URL through signup."""
    raw_url = request.form.get("original_url", "")
    user = current_user()
    try:
        if user:
            _, code = create_link(str(user["_id"]), {"original_url": raw_url})
            flash(f"Your short link is ready: /{code}", "success")
            return redirect(url_for("dashboard.links"))
        session["pending_url"] = normalize_url(raw_url)
    except LinkError as exc:
        flash(exc.message, "error")
        return redirect(url_for("pages.landing") + "#shorten")
    flash("Create a free account and your short link will be waiting.", "info")
    return redirect(url_for("auth.signup"))
