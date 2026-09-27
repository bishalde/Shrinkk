from flask import Blueprint, request, jsonify, session, flash, redirect, url_for
from datetime import datetime, timezone, timedelta
from utils.validators import is_valid_url, is_valid_alias
from services.shortener import generate_unique_code

link_bp = Blueprint("links", __name__)


def init_link_routes(link_model):

    @link_bp.route("/api/links/create", methods=["POST"])
    def create_link():
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for("auth.login_page"))

        data = request.get_json() if request.is_json else request.form
        original_url = data.get("original_url", "").strip()
        custom_alias = data.get("custom_alias", "").strip() or None
        expires_in = data.get("expires_in")  # hours

        if not original_url:
            if request.is_json:
                return jsonify({"error": "URL is required"}), 400
            flash("URL is required.", "error")
            return redirect(url_for("dashboard"))

        if not is_valid_url(original_url):
            if request.is_json:
                return jsonify({"error": "Invalid URL"}), 400
            flash("Please enter a valid URL (include http:// or https://).", "error")
            return redirect(url_for("dashboard"))

        if custom_alias:
            if not is_valid_alias(custom_alias):
                if request.is_json:
                    return jsonify({"error": "Invalid alias. Use 3-30 alphanumeric characters, hyphens, or underscores."}), 400
                flash("Invalid alias. Use 3-30 alphanumeric characters, hyphens, or underscores.", "error")
                return redirect(url_for("dashboard"))
            if link_model.find_by_short_code(custom_alias):
                if request.is_json:
                    return jsonify({"error": "Alias already taken"}), 409
                flash("That alias is already taken.", "error")
                return redirect(url_for("dashboard"))
            short_code = custom_alias
        else:
            short_code = generate_unique_code(link_model.collection)

        expires_at = None
        if expires_in:
            try:
                hours = int(expires_in)
                if hours > 0:
                    expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
            except (ValueError, TypeError):
                pass

        link_id = link_model.create_link(
            user_id=session["user_id"],
            original_url=original_url,
            short_code=short_code,
            custom_alias=custom_alias,
            expires_at=expires_at,
        )

        if request.is_json:
            return jsonify({
                "message": "Link created",
                "link_id": link_id,
                "short_code": short_code,
            }), 201

        flash("Link created successfully!", "success")
        return redirect(url_for("dashboard"))

    @link_bp.route("/api/links/", methods=["GET"])
    def list_links():
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        search = request.args.get("search")
        links = link_model.find_by_user(session["user_id"], search)
        result = []
        for link in links:
            result.append({
                "id": str(link["_id"]),
                "original_url": link["original_url"],
                "short_code": link["short_code"],
                "custom_alias": link.get("custom_alias"),
                "clicks": link["clicks"],
                "expires_at": link["expires_at"].isoformat() if link.get("expires_at") else None,
                "created_at": link["created_at"].isoformat(),
            })
        return jsonify(result)

    @link_bp.route("/api/links/<link_id>", methods=["PUT"])
    def update_link(link_id):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json()
        updates = {}
        if "original_url" in data:
            if not is_valid_url(data["original_url"]):
                return jsonify({"error": "Invalid URL"}), 400
            updates["original_url"] = data["original_url"]

        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        result = link_model.update_link(link_id, session["user_id"], updates)
        if result.modified_count == 0:
            return jsonify({"error": "Link not found or unauthorized"}), 404
        return jsonify({"message": "Link updated"})

    @link_bp.route("/api/links/<link_id>/delete", methods=["POST"])
    @link_bp.route("/api/links/<link_id>", methods=["DELETE"])
    def delete_link(link_id):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for("auth.login_page"))

        result = link_model.delete_link(link_id, session["user_id"])
        if result.deleted_count == 0:
            if request.is_json:
                return jsonify({"error": "Link not found or unauthorized"}), 404
            flash("Link not found.", "error")
            return redirect(url_for("dashboard"))

        if request.is_json:
            return jsonify({"message": "Link deleted"})
        flash("Link deleted.", "success")
        return redirect(url_for("dashboard"))

    return link_bp
