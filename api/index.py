"""Vercel entrypoint: every non-static request is rewritten here (see vercel.json).

Vercel detects the function by the top-level `app` assignment, so keep it a plain `app = ...`.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load():
    try:
        from app import create_app

        return create_app()
    except Exception as exc:  # misconfiguration: explain it instead of an opaque FUNCTION_INVOCATION_FAILED
        detail = re.sub(r"//[^/@\s]+@", "//***@", str(exc))  # never echo credentials from a URI
        # Which database variables this deployment sees (names only, never values).
        db_vars = [name for name in ("MONGO_URI", "MONGODB_URI") if os.getenv(name)]
        used = db_vars[0] if db_vars else "none (default localhost)"
        message = (
            f"Shrinkk is not configured correctly.\n\n{type(exc).__name__}: {detail}\n\n"
            f"Database address taken from: {used}\n"
            f"Database variables set in this deployment: {', '.join(db_vars) or 'none'}\n"
            f"Vercel environment: {os.getenv('VERCEL_ENV', 'unknown')}\n"
        ).encode()

        def not_configured(environ, start_response):
            start_response("503 Service Unavailable", [("Content-Type", "text/plain; charset=utf-8")])
            return [message]

        return not_configured


app = _load()
