"""Vercel entrypoint: every non-static request is rewritten here (see vercel.json)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

try:
    app = create_app()
except RuntimeError as exc:
    # Misconfiguration (e.g. SECRET_KEY missing): show why instead of an opaque FUNCTION_INVOCATION_FAILED.
    message = f"Shrinkk is not configured yet: {exc}\n".encode()

    def app(environ, start_response):
        start_response("503 Service Unavailable", [("Content-Type", "text/plain; charset=utf-8")])
        return [message]
