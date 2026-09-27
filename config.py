import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def _is_production():
    return os.getenv("VERCEL_ENV") == "production" or os.getenv("FLASK_ENV") == "production"


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "shrinkk")
    SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or "dev-insecure-change-me"
    # Optional canonical origin for short links; when unset, the domain the site was visited on is used.
    BASE_URL = os.getenv("BASE_URL", "").rstrip("/")

    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _is_production()

    # Vercel caps request bodies at 4.5 MB; avatars are limited to 2 MB in the upload handler.
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
    AVATAR_MAX_BYTES = 2 * 1024 * 1024

    WTF_CSRF_TIME_LIMIT = None

    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI", MONGO_URI if _is_production() else "memory://"
    )
    RATELIMIT_HEADERS_ENABLED = True

    STATS_CACHE_SECONDS = 600
    PRODUCTION = _is_production()
