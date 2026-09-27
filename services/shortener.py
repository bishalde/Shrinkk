import string
import random
import time

ALPHABET = string.ascii_letters + string.digits  # base62


def base62_encode(num):
    if num == 0:
        return ALPHABET[0]
    result = []
    while num:
        result.append(ALPHABET[num % 62])
        num //= 62
    return "".join(reversed(result))


def generate_short_code(length=6):
    return "".join(random.choices(ALPHABET, k=length))


def generate_unique_code(db_links, length=6, max_attempts=10):
    for _ in range(max_attempts):
        code = generate_short_code(length)
        if not db_links.find_one({"short_code": code}):
            return code
    timestamp_code = base62_encode(int(time.time() * 1000))
    return timestamp_code[-length:]
