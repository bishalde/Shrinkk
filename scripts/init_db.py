"""One-off database setup: create indexes and migrate pre-revamp analytics events.

    python scripts/init_db.py

Safe to re-run. Reads MONGO_URI / MONGO_DB from the environment (.env).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient  # noqa: E402

from config import Config  # noqa: E402
from models import Repos  # noqa: E402


def main():
    db = MongoClient(Config.MONGO_URI, tz_aware=True)[Config.MONGO_DB]
    repos = Repos.from_db(db)
    repos.ensure_indexes()
    print("Indexes ensured.")
    updated = repos.events.backfill_legacy(db.links)
    print(f"Backfilled {updated} legacy analytics events.")
    missing = db.users.count_documents({"username": {"$exists": False}})
    if missing:
        print(f"{missing} user(s) have no username yet; they'll be asked to pick one at next login.")


if __name__ == "__main__":
    main()
