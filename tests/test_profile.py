import io

from PIL import Image

from tests.test_links import CHROME, _create


def test_public_profile_shows_only_visible_bio_links(app, client, user):
    _create(client, title="Portfolio", on_profile=True)
    hidden = _create(client, title="Paused one", on_profile=True).json
    client.patch(f"/api/links/{hidden['id']}", json={"is_active": False})
    _create(client, title="Not on page")

    visitor = app.test_client()
    res = visitor.get("/@alice", headers=CHROME)
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Portfolio" in html and "?src=bio" in html
    assert "Paused one" not in html and "Not on page" not in html
    assert visitor.get("/@nobody").status_code == 404


def test_profile_views_skip_owner_and_bots(app, client, user, repos):
    client.get("/@alice", headers=CHROME)  # owner
    app.test_client().get("/@alice", headers={"User-Agent": "Twitterbot/1.0"})
    app.test_client().get("/@alice", headers=CHROME)
    assert repos.events.collection.count_documents({"type": "profile_view"}) == 1
    stats = repos.events.account_stats(user["_id"], 30)
    assert stats["profile_views"] == 1


def test_save_profile_socials_appearance(client, user, repos):
    assert client.post("/api/bio/profile", json={"display_name": "Alice", "bio": "Hi"}).status_code == 200
    assert client.post("/api/bio/profile", json={"bio": "x" * 161}).status_code == 400
    res = client.post("/api/bio/socials", json={"socials": {"github": "not valid!"}})
    assert res.status_code == 400 and "github" in res.json["fields"]
    client.post("/api/bio/socials", json={"socials": {"github": "alice", "email": "a@b.co"}})
    client.post("/api/bio/appearance", json={"appearance": {"theme": "sunset", "radius": "full", "bg": "#123456", "evil": "x"}})
    stored = repos.users.find_by_username("alice")
    assert stored["display_name"] == "Alice"
    assert stored["socials"] == {"github": "alice", "email": "a@b.co"}
    assert stored["appearance"] == {"theme": "sunset", "radius": "full", "bg": "#123456"}
    html = client.get("/@alice").get_data(as_text=True)
    assert "https://github.com/alice" in html and "--bio-bg:#123456" in html


def test_reorder_profile_links(client, user, repos):
    a = _create(client, title="A", on_profile=True).json["id"]
    b = _create(client, title="B", on_profile=True).json["id"]
    client.post("/api/bio/order", json={"ids": [b, a]})
    assert [l["title"] for l in repos.links.profile_links(user["_id"])] == ["B", "A"]


def _png(size=(800, 600)):
    buf = io.BytesIO()
    Image.new("RGB", size, "#1662FF").save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_avatar_upload_resizes_and_serves(client, user, repos):
    res = client.post("/api/bio/avatar", data={"avatar": (_png(), "me.png")}, content_type="multipart/form-data")
    assert res.status_code == 200
    img = client.get(res.json["avatar_url"])
    assert img.status_code == 200 and img.mimetype == "image/webp"
    assert Image.open(io.BytesIO(img.data)).size == (400, 400)
    assert "immutable" in img.headers["Cache-Control"]

    first_id = repos.users.find_by_username("alice")["avatar_id"]
    client.post("/api/bio/avatar", data={"avatar": (_png(), "me2.png")}, content_type="multipart/form-data")
    assert client.get(f"/media/avatar/{first_id}").status_code == 404  # old file cleaned up


def test_avatar_rejects_non_images(client, user):
    res = client.post("/api/bio/avatar", data={"avatar": (io.BytesIO(b"not an image"), "x.png")}, content_type="multipart/form-data")
    assert res.status_code == 400


def test_delete_account_removes_everything(client, user, repos):
    _create(client, custom_alias="bye")
    client.get("/bye", headers=CHROME)
    client.post("/api/bio/avatar", data={"avatar": (_png(), "me.png")}, content_type="multipart/form-data")
    res = client.post("/dashboard/settings/delete", data={"confirm": "wrong"})
    assert repos.users.find_by_username("alice") is not None
    res = client.post("/dashboard/settings/delete", data={"confirm": "alice"})
    assert res.status_code == 302
    assert repos.users.collection.count_documents({}) == 0
    assert repos.links.collection.count_documents({}) == 0
    assert repos.events.collection.count_documents({}) == 0
    assert not list(repos.media.fs.find({}))


def test_settings_changes(client, user, repos):
    client.post("/dashboard/settings/username", data={"username": "alice2"})
    assert repos.users.find_by_username("alice2")
    client.post("/dashboard/settings/password", data={"current_password": "wrong", "new_password": "newpassword1"})
    client.post("/dashboard/settings/password", data={"current_password": "password123", "new_password": "newpassword1"})
    client.post("/logout")
    assert client.post("/login", data={"email": "alice@example.com", "password": "newpassword1"}).status_code == 302


def test_all_pages_render(client, user):
    link_id = _create(client, on_profile=True).json["id"]
    client.get("/@alice", headers=CHROME)
    for path in ("/", "/dashboard", "/dashboard?days=7", "/dashboard/links", "/dashboard/links?q=exa&tag=x",
                 f"/dashboard/links/{link_id}", "/dashboard/bio", "/dashboard/analytics?days=90",
                 "/dashboard/settings", "/@alice"):
        res = client.get(path)
        assert res.status_code == 200, path
    client.post("/logout")
    for path in ("/", "/login", "/signup"):
        assert client.get(path).status_code == 200, path
