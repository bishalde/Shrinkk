from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from pymongo.errors import DuplicateKeyError

from extensions import limiter, repos
from models.user_model import UsernameTaken
from utils.helpers import consume_pending_link, current_user, login_required, login_user
from utils.validators import is_safe_next, is_valid_email, normalize_username, username_error

auth_bp = Blueprint("auth", __name__)

MIN_PASSWORD = 8


def check_username(username, exclude_user_id=None):
    """Error message for an unusable/taken username, or None."""
    error = username_error(username)
    if error:
        return error
    if not repos().users.username_available(username, exclude_user_id):
        return "That username is taken."
    return None


@auth_bp.route("/signup", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def signup():
    if current_user():
        return redirect(url_for("dashboard.home"))

    form = {"email": "", "username": request.args.get("username", "")}
    errors = {}
    if request.method == "POST":
        form = {
            "email": request.form.get("email", "").strip().lower(),
            "username": normalize_username(request.form.get("username")),
        }
        password = request.form.get("password", "")

        if not is_valid_email(form["email"]):
            errors["email"] = "Enter a valid email address."
        elif not repos().users.email_available(form["email"]):
            errors["email"] = "An account with this email already exists."
        if len(password) < MIN_PASSWORD:
            errors["password"] = f"Use at least {MIN_PASSWORD} characters."
        username_problem = check_username(form["username"])
        if username_problem:
            errors["username"] = username_problem

        if not errors:
            try:
                user_id = repos().users.create_user(form["email"], password, form["username"])
            except DuplicateKeyError:
                errors["username"] = "That email or username was just taken. Try again."
                return render_template("auth/signup.html", form=form, errors=errors), 400
            pending = session.get("pending_url")
            login_user(repos().users.find_by_id(user_id))
            if pending:
                session["pending_url"] = pending
            consume_pending_link(user_id)
            flash("Welcome to Shrinkk! Your bio page is live.", "success")
            return redirect(url_for("dashboard.home"))

    return render_template("auth/signup.html", form=form, errors=errors), 400 if errors else 200


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user():
        return redirect(url_for("dashboard.home"))

    next_url = request.values.get("next", "")
    email = ""
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = repos().users.find_by_email(email)
        if user and repos().users.verify_password(user["password"], password):
            pending = session.get("pending_url")
            login_user(user)
            if pending:
                session["pending_url"] = pending
            consume_pending_link(str(user["_id"]))
            return redirect(next_url if is_safe_next(next_url) else url_for("dashboard.home"))
        error = "Incorrect email or password."

    return render_template("auth/login.html", email=email, error=error, next=next_url), 401 if error else 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("pages.landing"))


@auth_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    user = current_user()
    if user.get("username"):
        return redirect(url_for("dashboard.home"))

    username, error = "", None
    if request.method == "POST":
        username = normalize_username(request.form.get("username"))
        error = check_username(username)
        if not error:
            try:
                repos().users.set_username(str(user["_id"]), username)
                if not user.get("display_name"):
                    repos().users.update_profile(str(user["_id"]), username, user.get("bio", ""))
                flash(f"You're all set — your page is live at /@{username}.", "success")
                return redirect(url_for("dashboard.home"))
            except UsernameTaken:
                error = "That username was just taken. Try another."
    return render_template("auth/onboarding.html", username=username, error=error)


@auth_bp.route("/api/username-available")
@limiter.limit("60 per minute")
def username_available():
    username = normalize_username(request.args.get("u"))
    user = current_user()
    error = check_username(username, exclude_user_id=str(user["_id"]) if user else None)
    return jsonify({"username": username, "available": error is None, "error": error})
