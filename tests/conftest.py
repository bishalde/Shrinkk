import os
import sys

import mongomock
import mongomock.gridfs
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

mongomock.gridfs.enable_gridfs_integration()


@pytest.fixture
def app():
    db = mongomock.MongoClient(tz_aware=True).db
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
            "BASE_URL": "http://shrinkk.test",
            "PRODUCTION": False,
        },
        db=db,
    )
    app.extensions["repos"].ensure_indexes()
    return app


@pytest.fixture
def repos(app):
    return app.extensions["repos"]


@pytest.fixture
def client(app):
    return app.test_client()


def signup(client, username="alice", email=None, password="password123"):
    return client.post("/signup", data={
        "username": username,
        "email": email or f"{username}@example.com",
        "password": password,
    })


@pytest.fixture
def user(client, repos):
    """A logged-in user; returns their document."""
    signup(client)
    return repos.users.find_by_username("alice")
