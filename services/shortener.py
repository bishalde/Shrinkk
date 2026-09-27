import secrets
import string

from utils.validators import RESERVED

ALPHABET = string.ascii_letters + string.digits  # base62


def generate_short_code(length=6):
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def generate_unique_code(link_model, length=6, max_attempts=10):
    """A random code not already in use; grows by one character after repeated collisions."""
    for attempt in range(max_attempts):
        code = generate_short_code(length + attempt // 5)
        if code.lower() not in RESERVED and not link_model.short_code_taken(code):
            return code
    raise RuntimeError("Could not generate a unique short code")
