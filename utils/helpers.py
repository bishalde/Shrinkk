from functools import wraps

from flask import current_app, flash, g, jsonify, redirect, request, session, url_for

from extensions import repos


def public_base_url():
    """Origin used in short links and QR codes: BASE_URL if configured, else the current host."""
    return current_app.config["BASE_URL"] or request.host_url.rstrip("/")


def current_user():
    """The logged-in user document (cached per request), or None."""
    if "current_user" not in g:
        user_id = session.get("user_id")
        g.current_user = repos().users.find_by_id(user_id) if user_id else None
        if user_id and g.current_user is None:
            session.clear()  # account was deleted elsewhere
    return g.current_user


def login_user(user):
    session.clear()
    session.permanent = True
    session["user_id"] = str(user["_id"])


def consume_pending_link(user_id):
    """Create the link a visitor typed on the landing page before signing up."""
    from services.link_service import LinkError, create_link

    url = session.pop("pending_url", None)
    if not url:
        return
    try:
        _, code = create_link(user_id, {"original_url": url})
        flash(f"Your short link is ready: /{code}", "success")
    except LinkError:
        pass


def _wants_json():
    return request.path.startswith("/api/") or request.is_json


def login_required(view):
    """Require a session. Accounts without a username are sent to onboarding first."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            if _wants_json():
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        if not user.get("username") and request.endpoint not in ("auth.onboarding", "auth.logout"):
            if _wants_json():
                return jsonify({"error": "Choose a username first"}), 403
            return redirect(url_for("auth.onboarding"))
        return view(*args, **kwargs)

    return wrapped


def json_error(message, status=400, **extra):
    return jsonify({"error": message, **extra}), status
