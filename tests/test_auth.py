from datetime import datetime, timezone

import bcrypt

from tests.conftest import signup


def test_signup_creates_user_and_logs_in(client, repos):
    res = signup(client)
    assert res.status_code == 302 and res.headers["Location"].endswith("/dashboard")
    user = repos.users.find_by_username("alice")
    assert user["email"] == "alice@example.com"
    assert client.get("/dashboard").status_code == 200


def test_signup_rejects_taken_and_reserved_usernames(client):
    signup(client)
    client.post("/logout")
    res = signup(client, username="alice", email="other@example.com")
    assert res.status_code == 400 and b"That username is taken" in res.data
    res = signup(client, username="settings", email="x@example.com")
    assert b"reserved" in res.data


def test_login_and_bad_password(client):
    signup(client)
    client.post("/logout")
    res = client.post("/login", data={"email": "alice@example.com", "password": "wrong-pass"})
    assert res.status_code == 401
    res = client.post("/login", data={"email": "alice@example.com", "password": "password123"})
    assert res.status_code == 302


def test_login_ignores_offsite_next(client):
    signup(client)
    client.post("/logout")
    res = client.post("/login?next=https://evil.com", data={"email": "alice@example.com", "password": "password123"})
    assert res.headers["Location"].endswith("/dashboard")
    client.post("/logout")
    res = client.post("/login?next=/dashboard/links", data={"email": "alice@example.com", "password": "password123"})
    assert res.headers["Location"].endswith("/dashboard/links")


def test_dashboard_requires_login(client):
    res = client.get("/dashboard/links")
    assert res.status_code == 302 and "/login" in res.headers["Location"]
    assert client.get("/api/bio/order").status_code in (401, 405)
    assert client.post("/api/bio/order", json={"ids": []}).status_code == 401


def test_legacy_user_without_username_is_onboarded(client, repos):
    repos.users.collection.insert_one({
        "email": "old@example.com",
        "password": bcrypt.hashpw(b"password123", bcrypt.gensalt()),
        "created_at": datetime.now(timezone.utc),
    })
    client.post("/login", data={"email": "old@example.com", "password": "password123"})
    res = client.get("/dashboard")
    assert res.status_code == 302 and res.headers["Location"].endswith("/onboarding")
    res = client.post("/onboarding", data={"username": "oldtimer"})
    assert res.headers["Location"].endswith("/dashboard")
    assert repos.users.find_by_username("oldtimer")["display_name"] == "oldtimer"


def test_pending_landing_url_is_created_after_signup(client, repos):
    res = client.post("/shorten", data={"original_url": "example.com/some/long/path"})
    assert res.headers["Location"].endswith("/signup")
    signup(client)
    links = repos.links.find_by_user(repos.users.find_by_username("alice")["_id"])
    assert [l["original_url"] for l in links] == ["https://example.com/some/long/path"]


def test_username_availability_api(client, user):
    assert client.get("/api/username-available?u=alice").json["available"] is True  # own name
    assert client.get("/api/username-available?u=admin").json["available"] is False
    assert client.get("/api/username-available?u=newname").json["available"] is True


def test_landing_rotates_headline(client):
    halves = ["for everyone", "bigger reach", "for everything you share", "track every click", "in one bio link"]
    seen = {h for _ in range(40) for h in halves if h in client.get("/").get_data(as_text=True)}
    assert len(seen) > 1
