"""JSON endpoints used by the dashboard's interactive pieces (bio editor, toggles, QR studio)."""
from flask import Blueprint, current_app, jsonify, request, url_for

from extensions import limiter, repos
from services import socials, themes
from services.images import InvalidImage, make_avatar
from services.link_service import LinkError, create_link, delete_links, update_link
from utils.helpers import current_user, json_error, login_required
from utils.serializers import serialize_link

api_bp = Blueprint("api", __name__, url_prefix="/api")
api_bp.decorators = [limiter.limit("120 per minute")]

MAX_BIO = 160
MAX_NAME = 50


def _uid():
    return str(current_user()["_id"])


def _json():
    return request.get_json(silent=True) or {}


@api_bp.route("/links", methods=["POST"])
@login_required
def create():
    try:
        link_id, _ = create_link(_uid(), _json())
    except LinkError as exc:
        return json_error(exc.message, exc.status)
    return jsonify(serialize_link(repos().links.find_by_id(link_id))), 201


@api_bp.route("/links/<link_id>", methods=["PATCH"])
@login_required
def patch(link_id):
    link = repos().links.find_owned(link_id, _uid())
    if not link:
        return json_error("Link not found", 404)
    try:
        update_link(link, _json())
    except LinkError as exc:
        return json_error(exc.message, exc.status)
    return jsonify(serialize_link(repos().links.find_by_id(link_id)))


@api_bp.route("/links/<link_id>", methods=["DELETE"])
@login_required
def delete(link_id):
    if not delete_links(_uid(), [link_id]):
        return json_error("Link not found", 404)
    return jsonify({"deleted": link_id})


@api_bp.route("/bio/order", methods=["POST"])
@login_required
def reorder():
    ids = _json().get("ids")
    if not isinstance(ids, list):
        return json_error("ids must be a list")
    repos().links.reorder_profile(_uid(), [str(i) for i in ids])
    return jsonify({"ok": True})


@api_bp.route("/bio/profile", methods=["POST"])
@login_required
def save_profile():
    data = _json()
    display_name = (data.get("display_name") or "").strip()
    bio = (data.get("bio") or "").strip()
    if len(display_name) > MAX_NAME:
        return json_error(f"Name must be at most {MAX_NAME} characters.")
    if len(bio) > MAX_BIO:
        return json_error(f"Bio must be at most {MAX_BIO} characters.")
    repos().users.update_profile(_uid(), display_name, bio)
    return jsonify({"display_name": display_name, "bio": bio})


@api_bp.route("/bio/socials", methods=["POST"])
@login_required
def save_socials():
    cleaned, errors = socials.clean(_json().get("socials"))
    if errors:
        return json_error("Some social links need fixing.", 400, fields=errors)
    repos().users.set_socials(_uid(), cleaned)
    return jsonify({"socials": cleaned})


@api_bp.route("/bio/appearance", methods=["POST"])
@login_required
def save_appearance():
    appearance = themes.clean(_json().get("appearance"))
    repos().users.set_appearance(_uid(), appearance)
    return jsonify({"appearance": appearance})


@api_bp.route("/bio/avatar", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def upload_avatar():
    upload = request.files.get("avatar")
    if not upload:
        return json_error("Choose an image to upload.")
    data = upload.read(current_app.config["AVATAR_MAX_BYTES"] + 1)
    if len(data) > current_app.config["AVATAR_MAX_BYTES"]:
        return json_error("Images must be 2 MB or smaller.", 413)
    try:
        webp = make_avatar(data)
    except InvalidImage as exc:
        return json_error(str(exc))

    r = repos()
    user = current_user()
    new_id = r.media.save(webp, "image/webp", _uid())
    r.users.set_avatar(_uid(), new_id)
    r.media.delete(user.get("avatar_id"))
    return jsonify({"avatar_url": url_for("public.avatar", file_id=new_id)})


@api_bp.route("/bio/avatar", methods=["DELETE"])
@login_required
def remove_avatar():
    user = current_user()
    repos().media.delete(user.get("avatar_id"))
    repos().users.set_avatar(_uid(), None)
    return jsonify({"avatar_url": None})
