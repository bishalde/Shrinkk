"""Public, unauthenticated routes: bio pages, QR codes, avatars and short-link redirects."""
from flask import Blueprint, abort, current_app, redirect, render_template, request, send_file, url_for

from extensions import limiter, repos
from services import socials, themes
from services.qr_generator import DEFAULT_BG, DEFAULT_FG, generate_png, generate_svg
from services.request_info import visitor
from utils.helpers import current_user
from utils.validators import is_hex_color

public_bp = Blueprint("public", __name__)

QR_FORMATS = {"png": "image/png", "svg": "image/svg+xml"}


def _qr_response(data, name, fmt, fg, bg):
    fg = request.args.get("fg", fg)
    bg = request.args.get("bg", bg)
    fg = fg if is_hex_color(fg) else DEFAULT_FG
    bg = bg if is_hex_color(bg) else DEFAULT_BG
    buffer = generate_svg(data, fg, bg) if fmt == "svg" else generate_png(data, fg, bg)
    response = send_file(
        buffer,
        mimetype=QR_FORMATS[fmt],
        as_attachment=bool(request.args.get("dl")),
        download_name=f"{name}.{fmt}",
    )
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@public_bp.route("/@<username>")
def profile(username):
    user = repos().users.find_by_username(username.lower())
    if not user:
        abort(404)
    uid = str(user["_id"])
    viewer = current_user()
    is_owner = viewer is not None and str(viewer["_id"]) == uid

    info = visitor()
    if not info["is_bot"] and not is_owner:
        repos().events.log_profile_view(uid, info)

    return render_template(
        "public/profile.html",
        profile=user,
        links=repos().links.profile_links(uid, public=True),
        socials=socials.for_display(user.get("socials")),
        look=themes.resolve(user.get("appearance")),
        avatar_url=url_for("public.avatar", file_id=user["avatar_id"]) if user.get("avatar_id") else None,
        profile_url=f"{current_app.config['BASE_URL']}/@{user['username']}",
        is_owner=is_owner,
    )


@public_bp.route("/@<username>/qr.<fmt>")
def profile_qr(username, fmt):
    user = repos().users.find_by_username(username.lower())
    if not user or fmt not in QR_FORMATS:
        abort(404)
    url = f"{current_app.config['BASE_URL']}/@{user['username']}"
    return _qr_response(url, f"shrinkk-{user['username']}", fmt, DEFAULT_FG, DEFAULT_BG)


@public_bp.route("/qr/<short_code>")
def legacy_link_qr(short_code):
    """Pre-revamp QR URLs had no extension."""
    return link_qr(short_code, "png")


@public_bp.route("/qr/<short_code>.<fmt>")
def link_qr(short_code, fmt):
    link = repos().links.find_by_short_code(short_code)
    if not link or fmt not in QR_FORMATS:
        abort(404)
    url = f"{current_app.config['BASE_URL']}/{short_code}?src=qr"
    qr = link.get("qr") or {}
    return _qr_response(url, f"qr-{short_code}", fmt, qr.get("fg") or DEFAULT_FG, qr.get("bg") or DEFAULT_BG)


@public_bp.route("/media/avatar/<file_id>")
def avatar(file_id):
    stored = repos().media.get(file_id)
    if not stored:
        abort(404)
    response = send_file(stored, mimetype=(stored.metadata or {}).get("content_type", "image/webp"))
    # A new upload gets a new id, so the old URL's content never changes.
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


@public_bp.route("/<short_code>")
@limiter.limit("120 per minute")
def redirect_short(short_code):
    links = repos().links
    link = links.find_by_short_code(short_code)
    if not link:
        abort(404)
    if links.is_expired(link):
        return render_template("errors/error.html", code=410, title="This link has expired",
                               message="The owner set this link to stop working after a certain date."), 410
    if not link.get("is_active", True):
        return render_template("errors/error.html", code=410, title="This link is paused",
                               message="The owner has temporarily turned this link off."), 410

    info = visitor()
    if not info["is_bot"]:
        repos().events.log_click(link, info)
        links.increment_clicks(str(link["_id"]))

    response = redirect(link["original_url"], code=302)
    response.headers["Cache-Control"] = "no-store"
    return response
