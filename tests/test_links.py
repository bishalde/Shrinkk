import io
from datetime import datetime, timedelta, timezone

from tests.conftest import signup

CHROME = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}


def _create(client, **data):
    return client.post("/api/links", json={"original_url": "https://example.com", **data})


def test_create_link_with_alias_tags_and_title(client, user):
    res = _create(client, custom_alias="launch", title="Launch", tags="News, launch ,news")
    assert res.status_code == 201
    body = res.json
    assert body["short_code"] == "launch"
    assert body["tags"] == ["news", "launch"]
    assert body["short_url"] == "http://shrinkk.test/launch"


def test_create_link_validation(client, user):
    assert _create(client, original_url="not a url").status_code == 400
    assert _create(client, custom_alias="dashboard").status_code == 400
    assert _create(client, original_url="http://shrinkk.test/abc").status_code == 400
    _create(client, custom_alias="taken")
    assert _create(client, custom_alias="taken").status_code == 409


def test_form_create_and_edit(client, user, repos):
    client.post("/dashboard/links", data={"original_url": "https://a.com", "custom_alias": "aaa"})
    link = repos.links.find_by_short_code("aaa")
    res = client.post(f"/dashboard/links/{link['_id']}", data={
        "original_url": "https://b.com", "custom_alias": "bbb", "title": "B", "tags": "x", "expires_on": "",
    })
    assert res.status_code == 302
    link = repos.links.find_by_id(link["_id"])
    assert (link["original_url"], link["short_code"], link["title"], link["on_profile"]) == ("https://b.com", "bbb", "B", False)


def test_users_cannot_touch_each_others_links(app, client, user):
    link_id = _create(client).json["id"]
    other = app.test_client()
    signup(other, username="bob")
    assert other.patch(f"/api/links/{link_id}", json={"title": "pwned"}).status_code == 404
    assert other.delete(f"/api/links/{link_id}").status_code == 404
    assert other.get(f"/dashboard/links/{link_id}").status_code == 404


def test_redirect_logs_click_with_source(client, user, repos):
    link = _create(client, custom_alias="goto").json
    res = client.get("/goto?src=bio", headers={**CHROME, "X-Vercel-IP-Country": "de", "X-Vercel-IP-City": "M%C3%BCnchen"})
    assert res.status_code == 302 and res.headers["Location"] == "https://example.com"
    event = repos.events.collection.find_one({"type": "click"})
    assert (event["source"], event["country"], event["city"], event["device"]) == ("bio", "DE", "München", "Desktop")
    assert repos.links.find_by_id(link["id"])["clicks"] == 1


def test_bots_are_redirected_but_not_counted(client, user, repos):
    link = _create(client, custom_alias="botx").json
    res = client.get("/botx", headers={"User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)"})
    assert res.status_code == 302
    assert repos.links.find_by_id(link["id"])["clicks"] == 0


def test_paused_and_expired_links_return_410(client, user, repos):
    link = _create(client, custom_alias="paused").json
    client.patch(f"/api/links/{link['id']}", json={"is_active": False})
    assert client.get("/paused").status_code == 410
    expired = _create(client, custom_alias="oldie").json
    repos.links.collection.update_one({"short_code": "oldie"}, {"$set": {"expires_at": datetime.now(timezone.utc) - timedelta(days=1)}})
    assert client.get("/oldie").status_code == 410
    assert expired["expired"] is False
    assert client.get("/missing-code").status_code == 404


def test_bulk_actions(client, user, repos):
    ids = [_create(client).json["id"] for _ in range(3)]
    client.post("/dashboard/links/bulk", data={"action": "tag", "ids": ids[:2], "tag": "Promo"})
    assert repos.links.tags_for_user(user["_id"]) == ["promo"]
    client.post("/dashboard/links/bulk", data={"action": "deactivate", "ids": ids})
    assert all(not l["is_active"] for l in repos.links.find_by_user(user["_id"]))
    client.post("/dashboard/links/bulk", data={"action": "delete", "ids": ids[:2]})
    assert repos.links.count_by_user(user["_id"]) == 1


def test_delete_removes_events(client, user, repos):
    link = _create(client, custom_alias="gone").json
    client.get("/gone", headers=CHROME)
    assert repos.events.collection.count_documents({}) == 1
    client.delete(f"/api/links/{link['id']}")
    assert repos.events.collection.count_documents({}) == 0


def test_qr_png_and_svg_with_colors(client, user):
    _create(client, custom_alias="qr1")
    png = client.get("/qr/qr1.png?fg=%23FF0000")
    assert png.status_code == 200 and png.data[:8] == b"\x89PNG\r\n\x1a\n"
    svg = client.get("/qr/qr1.svg?fg=%231662FF&dl=1")
    assert b'fill="#1662FF"' in svg.data
    assert "attachment" in svg.headers["Content-Disposition"]
    assert client.get("/qr/qr1").status_code == 200  # legacy URL


def test_link_stats(client, user, repos):
    link = _create(client, custom_alias="stats1").json
    for _ in range(3):
        client.get("/stats1?src=qr", headers=CHROME)
    stats = repos.events.link_stats(link["id"], 7)
    assert stats["total"] == 3
    assert stats["series"][-1]["count"] == 3 and len(stats["series"]) == 7
    assert stats["by_source"] == [{"label": "qr", "count": 3}]
