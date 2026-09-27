import os
from datetime import datetime, timezone

from flask import Flask, render_template, request
from pymongo import MongoClient
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from extensions import csrf, limiter
from models import Repos
from utils.helpers import current_user, public_base_url

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_app(config_overrides=None, db=None):
    # Static files live in public/ so Vercel serves them from its CDN; Flask serves them locally.
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, "public", "static"),
        static_url_path="/static",
    )
    app.config.from_object(Config)
    app.config.update(config_overrides or {})

    if app.config["PRODUCTION"] and app.config["SECRET_KEY"] == "dev-insecure-change-me":
        raise RuntimeError("Set SECRET_KEY in the environment before running in production.")

    if os.getenv("VERCEL"):
        # Trust Vercel's proxy for the real scheme and host (https://shrinkk.vercel.app, custom domains).
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    if db is None:
        db = _connect(app.config["MONGO_URI"], app.config["MONGO_DB"])
    app.extensions["repos"] = Repos.from_db(db)

    csrf.init_app(app)
    limiter.init_app(app)

    from routes.api import api_bp
    from routes.auth_routes import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.pages import pages_bp
    from routes.public import public_bp

    for bp in (pages_bp, auth_bp, dashboard_bp, api_bp, public_bp):
        app.register_blueprint(bp)

    _register_template_helpers(app)
    _register_error_handlers(app)
    return app


def _connect(uri, db_name):
    if uri.startswith("mongomock://"):
        # In-memory database for local development without MongoDB (data is lost on restart).
        import mongomock
        import mongomock.gridfs

        mongomock.gridfs.enable_gridfs_integration()
        return mongomock.MongoClient(tz_aware=True)[db_name]
    return MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=5000)[db_name]


def _register_template_helpers(app):
    from utils.formatting import register_filters

    register_filters(app)

    @app.context_processor
    def inject_globals():
        base_url = public_base_url()
        return {
            "current_user": current_user(),
            "base_url": base_url,
            "base_host": base_url.split("://", 1)[-1],
            "now_year": datetime.now(timezone.utc).year,
        }


def _register_error_handlers(app):
    from flask import jsonify
    from flask_wtf.csrf import CSRFError

    def wants_json():
        return request.path.startswith("/api/") or request.is_json

    @app.errorhandler(404)
    def not_found(_e):
        if wants_json():
            return jsonify({"error": "Not found"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"error": "That file is too large."}), 413

    @app.errorhandler(429)
    def rate_limited(_e):
        if wants_json():
            return jsonify({"error": "Too many requests. Try again in a minute."}), 429
        return render_template("errors/error.html", code=429, title="Slow down",
                               message="Too many requests. Try again in a minute."), 429

    @app.errorhandler(CSRFError)
    def csrf_failed(_e):
        if wants_json():
            return jsonify({"error": "Your session expired. Refresh the page and try again."}), 400
        return render_template("errors/error.html", code=400, title="Session expired",
                               message="Refresh the page and try again."), 400

    @app.errorhandler(500)
    def server_error(_e):
        if wants_json():
            return jsonify({"error": "Something went wrong."}), 500
        return render_template("errors/error.html", code=500, title="Something went wrong",
                               message="We hit an unexpected error. Please try again."), 500


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)), debug=True)
