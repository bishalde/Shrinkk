from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from utils.validators import is_valid_email

auth_bp = Blueprint("auth", __name__)


def init_auth_routes(user_model):

    @auth_bp.route("/signup", methods=["GET"])
    def signup_page():
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return render_template("signup.html")

    @auth_bp.route("/login", methods=["GET"])
    def login_page():
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @auth_bp.route("/api/auth/register", methods=["POST"])
    def register():
        data = request.get_json() if request.is_json else request.form
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not email or not password:
            if request.is_json:
                return jsonify({"error": "Email and password required"}), 400
            flash("Email and password are required.", "error")
            return redirect(url_for("auth.signup_page"))

        if not is_valid_email(email):
            if request.is_json:
                return jsonify({"error": "Invalid email format"}), 400
            flash("Invalid email format.", "error")
            return redirect(url_for("auth.signup_page"))

        if len(password) < 6:
            if request.is_json:
                return jsonify({"error": "Password must be at least 6 characters"}), 400
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("auth.signup_page"))

        if user_model.find_by_email(email):
            if request.is_json:
                return jsonify({"error": "Email already registered"}), 409
            flash("Email already registered.", "error")
            return redirect(url_for("auth.signup_page"))

        user_id = user_model.create_user(email, password)
        session["user_id"] = user_id
        session["email"] = email.lower().strip()

        if request.is_json:
            return jsonify({"message": "User created", "user_id": user_id}), 201
        return redirect(url_for("dashboard"))

    @auth_bp.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json() if request.is_json else request.form
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not email or not password:
            if request.is_json:
                return jsonify({"error": "Email and password required"}), 400
            flash("Email and password are required.", "error")
            return redirect(url_for("auth.login_page"))

        user = user_model.find_by_email(email)
        if not user or not user_model.verify_password(user["password"], password):
            if request.is_json:
                return jsonify({"error": "Invalid credentials"}), 401
            flash("Invalid email or password.", "error")
            return redirect(url_for("auth.login_page"))

        session["user_id"] = str(user["_id"])
        session["email"] = user["email"]

        if request.is_json:
            return jsonify({"message": "Login successful", "user_id": str(user["_id"])}), 200

        next_url = request.args.get("next", url_for("dashboard"))
        return redirect(next_url)

    @auth_bp.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("landing"))

    @auth_bp.route("/api/auth/profile", methods=["GET"])
    def profile():
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        user = user_model.find_by_id(session["user_id"])
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "user_id": str(user["_id"]),
            "email": user["email"],
            "created_at": user["created_at"].isoformat(),
        })

    return auth_bp
