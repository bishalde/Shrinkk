from flask import current_app
from flask_limiter import Limiter
from flask_wtf.csrf import CSRFProtect

from services.request_info import client_ip

csrf = CSRFProtect()
limiter = Limiter(key_func=client_ip, default_limits=["300 per minute"])


def repos():
    """The model registry attached to the running app (see app.create_app)."""
    return current_app.extensions["repos"]
