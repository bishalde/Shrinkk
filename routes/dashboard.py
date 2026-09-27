from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from extensions import repos
from models.user_model import UsernameTaken
from routes.auth_routes import MIN_PASSWORD, check_username
from services import socials, themes
from services.link_service import LinkError, create_link, delete_links, parse_tags, update_link
from utils.helpers import current_user, login_required
from utils.serializers import serialize_link
from utils.validators import is_valid_email, normalize_username

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

RANGES = (7, 30, 90)


def _uid():
    return str(current_user()["_id"])


def _days():
    days = request.args.get("days", type=int)
    return days if days in RANGES else 30


def _back_to_links():
    target = request.form.get("return_to", "")
    return redirect(target if target.startswith("/dashboard") else url_for("dashboard.links"))


@dashboard_bp.route("")
@login_required
def home():
    uid = _uid()
    r = repos()
    stats = r.events.account_stats(uid, _days())
    return render_template(
        "dashboard/home.html",
        stats=stats,
        total_links=r.links.count_by_user(uid),
        total_clicks=r.links.total_clicks(uid),
        top_links=[serialize_link(l) for l in r.links.top_by_user(uid, 5)],
        days=stats["days"],
    )


# --- links -------------------------------------------------------------------

@dashboard_bp.route("/links")
@login_required
def links():
    uid = _uid()
    search = request.args.get("q", "").strip()
    tag = request.args.get("tag", "").strip()
    found = repos().links.find_by_user(uid, search or None, tag or None)
    return render_template(
        "dashboard/links.html",
        links=[serialize_link(l) for l in found],
        tags=repos().links.tags_for_user(uid),
        search=search,
        active_tag=tag,
    )


@dashboard_bp.route("/links", methods=["POST"])
@login_required
def create_link_form():
    try:
        _, code = create_link(_uid(), request.form)
        flash(f"Link created: /{code}", "success")
    except LinkError as exc:
        flash(exc.message, "error")
    return _back_to_links()


@dashboard_bp.route("/links/<link_id>", methods=["POST"])
@login_required
def edit_link_form(link_id):
    link = repos().links.find_owned(link_id, _uid())
    if not link:
        abort(404)
    data = request.form.to_dict()
    # Unchecked checkboxes are absent from form posts.
    data.setdefault("on_profile", "")
    try:
        update_link(link, data)
        flash("Link updated.", "success")
    except LinkError as exc:
        flash(exc.message, "error")
    return _back_to_links()


@dashboard_bp.route("/links/<link_id>/delete", methods=["POST"])
@login_required
def delete_link_form(link_id):
    if delete_links(_uid(), [link_id]):
        flash("Link deleted.", "success")
    else:
        flash("Link not found.", "error")
    return redirect(url_for("dashboard.links"))


@dashboard_bp.route("/links/bulk", methods=["POST"])
@login_required
def bulk_links():
    uid = _uid()
    ids = request.form.getlist("ids")
    action = request.form.get("action")
    if not ids:
        flash("Select at least one link.", "error")
        return _back_to_links()

    r = repos()
    if action == "delete":
        count = delete_links(uid, ids)
        flash(f"Deleted {count} link{'s' if count != 1 else ''}.", "success")
    elif action in ("activate", "deactivate"):
        r.links.bulk_update(ids, uid, {"is_active": action == "activate"})
        flash(f"{'Activated' if action == 'activate' else 'Paused'} {len(ids)} link(s).", "success")
    elif action == "add_to_bio":
        for link_id in ids:
            r.links.update_link(link_id, uid, {"on_profile": True})
        flash("Added to your bio page.", "success")
    elif action == "tag":
        tags = parse_tags(request.form.get("tag", ""))
        if not tags:
            flash("Enter a tag name.", "error")
        else:
            r.links.bulk_add_tag(ids, uid, tags[0])
            flash(f"Tagged {len(ids)} link(s) with “{tags[0]}”.", "success")
    else:
        flash("Unknown action.", "error")
    return _back_to_links()


@dashboard_bp.route("/links/<link_id>")
@login_required
def link_detail(link_id):
    link = repos().links.find_owned(link_id, _uid())
    if not link:
        abort(404)
    days = _days()
    return render_template(
        "dashboard/link_detail.html",
        link=serialize_link(link),
        stats=repos().events.link_stats(link_id, days),
        days=days,
    )


# --- bio page ----------------------------------------------------------------

@dashboard_bp.route("/bio")
@login_required
def bio():
    uid = _uid()
    user = current_user()
    all_links = repos().links.find_by_user(uid)
    profile_links = sorted((l for l in all_links if l.get("on_profile")), key=lambda l: l.get("profile_order", 0))
    return render_template(
        "dashboard/bio.html",
        profile_links=[serialize_link(l) for l in profile_links],
        other_links=[serialize_link(l) for l in all_links if not l.get("on_profile")],
        profile={
            "username": user["username"],
            "display_name": user.get("display_name", ""),
            "bio": user.get("bio", ""),
            "avatar_url": url_for("public.avatar", file_id=user["avatar_id"]) if user.get("avatar_id") else None,
        },
        socials_values=user.get("socials", {}),
        networks=socials.NETWORKS,
        appearance=themes.clean(user.get("appearance")),
        theme_config=themes.editor_config(),
    )


# --- analytics -----------------------------------------------------------------

@dashboard_bp.route("/analytics")
@login_required
def analytics():
    uid = _uid()
    stats = repos().events.account_stats(uid, _days())
    links_by_id = {
        str(l["_id"]): serialize_link(l)
        for l in repos().links.find_by_user(uid)
    }
    top = [{**links_by_id[t["link_id"]], "period_clicks": t["count"]}
           for t in stats["top_links"] if t["link_id"] in links_by_id]
    return render_template("dashboard/analytics.html", stats=stats, top_links=top, days=stats["days"])


# --- settings --------------------------------------------------------------------

@dashboard_bp.route("/settings")
@login_required
def settings():
    return render_template("dashboard/settings.html")


@dashboard_bp.route("/settings/username", methods=["POST"])
@login_required
def change_username():
    username = normalize_username(request.form.get("username"))
    user = current_user()
    if username == user.get("username"):
        return redirect(url_for("dashboard.settings"))
    error = check_username(username, exclude_user_id=_uid())
    if error:
        flash(error, "error")
    else:
        try:
            repos().users.set_username(_uid(), username)
            flash(f"Username changed. Your page is now at /@{username}.", "success")
        except UsernameTaken:
            flash("That username was just taken.", "error")
    return redirect(url_for("dashboard.settings"))


@dashboard_bp.route("/settings/email", methods=["POST"])
@login_required
def change_email():
    email = request.form.get("email", "").strip().lower()
    if not is_valid_email(email):
        flash("Enter a valid email address.", "error")
    elif not repos().users.email_available(email, exclude_user_id=_uid()):
        flash("That email is already in use.", "error")
    elif not repos().users.verify_password(current_user()["password"], request.form.get("password", "")):
        flash("Your current password is incorrect.", "error")
    else:
        repos().users.set_email(_uid(), email)
        flash("Email updated.", "success")
    return redirect(url_for("dashboard.settings"))


@dashboard_bp.route("/settings/password", methods=["POST"])
@login_required
def change_password():
    current_pw = request.form.get("current_password", "")
    new_pw = request.form.get("new_password", "")
    if not repos().users.verify_password(current_user()["password"], current_pw):
        flash("Your current password is incorrect.", "error")
    elif len(new_pw) < MIN_PASSWORD:
        flash(f"New password must be at least {MIN_PASSWORD} characters.", "error")
    else:
        repos().users.set_password(_uid(), new_pw)
        flash("Password updated.", "success")
    return redirect(url_for("dashboard.settings"))


@dashboard_bp.route("/settings/delete", methods=["POST"])
@login_required
def delete_account():
    user = current_user()
    if request.form.get("confirm", "").strip().lower() != user["username"]:
        flash("Type your username exactly to confirm.", "error")
        return redirect(url_for("dashboard.settings"))
    uid = _uid()
    r = repos()
    r.media.delete(user.get("avatar_id"))
    r.events.delete_for_user(uid)
    r.links.delete_all_for_user(uid)
    r.users.delete(uid)
    session.clear()
    flash("Your account and all its data have been deleted.", "success")
    return redirect(url_for("pages.landing"))
