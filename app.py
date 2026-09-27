from flask import Flask, redirect, render_template, session, request, send_file, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from config import Config

from models.user_model import UserModel
from models.link_model import LinkModel
from models.analytics_model import AnalyticsModel

from routes.auth_routes import auth_bp, init_auth_routes
from routes.link_routes import link_bp, init_link_routes
from routes.analytics_routes import analytics_bp, init_analytics_routes

from services.analytics import parse_request_data
from services.qr_generator import generate_qr


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    limiter = Limiter(get_remote_address, app=app, default_limits=["200 per minute"])

    # MongoDB
    client = MongoClient(app.config["MONGO_URI"])
    db = client.shrinkk

    # Models
    user_model = UserModel(db)
    link_model = LinkModel(db)
    analytics_model = AnalyticsModel(db)

    # Init and register blueprints
    init_auth_routes(user_model)
    init_link_routes(link_model)
    init_analytics_routes(analytics_model, link_model)

    app.register_blueprint(auth_bp)
    app.register_blueprint(link_bp)
    app.register_blueprint(analytics_bp)

    # --- Page routes ---

    @app.route("/")
    def landing():
        if "user_id" in session:
            return redirect("/dashboard")
        return render_template("landing.html")

    @app.route("/dashboard")
    def dashboard():
        if "user_id" not in session:
            return redirect("/login")
        links = link_model.find_by_user(session["user_id"], request.args.get("search"))
        total_clicks = sum(l["clicks"] for l in links)
        return render_template(
            "dashboard.html",
            links=links,
            total_links=len(links),
            total_clicks=total_clicks,
            base_url=app.config["BASE_URL"],
            email=session.get("email"),
        )

    @app.route("/dashboard/link/<link_id>")
    def link_detail(link_id):
        if "user_id" not in session:
            return redirect("/login")
        link = link_model.find_by_id(link_id)
        if not link or str(link["user_id"]) != session["user_id"]:
            abort(404)
        stats = analytics_model.get_stats(link_id)
        return render_template(
            "link_detail.html",
            link=link,
            stats=stats,
            base_url=app.config["BASE_URL"],
            email=session.get("email"),
        )

    # --- QR code endpoint ---

    @app.route("/qr/<short_code>")
    def qr_code(short_code):
        link = link_model.find_by_short_code(short_code)
        if not link:
            abort(404)
        url = f"{app.config['BASE_URL']}/{short_code}"
        buffer = generate_qr(url)
        return send_file(buffer, mimetype="image/png", download_name=f"qr-{short_code}.png")

    # --- Redirect handler ---

    @app.route("/<short_code>")
    @limiter.limit("60 per minute")
    def redirect_short(short_code):
        # Skip static-like paths
        if short_code in ("favicon.ico", "robots.txt"):
            abort(404)

        link = link_model.find_by_short_code(short_code)
        if not link:
            return render_template("errors/404.html"), 404

        if link_model.is_expired(link):
            return render_template("errors/expired.html", link=link), 410

        # Log analytics
        data = parse_request_data(request)
        analytics_model.log_click(
            link_id=str(link["_id"]),
            ip=data["ip"],
            country=data["country"],
            city=data["city"],
            device=data["device"],
            browser=data["browser"],
            os=data["os"],
            referrer=data["referrer"],
        )
        link_model.increment_clicks(str(link["_id"]))

        return redirect(link["original_url"], code=302)

    # --- Error handlers ---

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)
