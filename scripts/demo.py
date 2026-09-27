"""Run Shrinkk locally with an in-memory database pre-filled with demo data.

    python scripts/demo.py            # http://localhost:8080  (log in: demo@shrinkk.app / demo12345)

Seeds three profiles: /@bishal (the account you log in as), /@sima and /@basak.
Nothing touches a real MongoDB; everything resets when the process stops.
"""
import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mongomock
import mongomock.gridfs
from bson import ObjectId

mongomock.gridfs.enable_gridfs_integration()

from app import create_app  # noqa: E402

db = mongomock.MongoClient(tz_aware=True).db
PORT = int(os.getenv("PORT", 8080))
app = create_app({"RATELIMIT_ENABLED": False, "BASE_URL": f"http://localhost:{PORT}"}, db=db)
r = app.extensions["repos"]
r.ensure_indexes()

random.seed(7)
countries = ["US", "IN", "DE", "GB", "BR", "CA", "FR", "JP"]
refs = [None, "instagram.com", "t.co", "youtube.com", "google.com", "linkedin.com"]
now = datetime.now(timezone.utc)


def recent():
    return now - timedelta(days=random.betavariate(1.2, 3) * 60, hours=random.random() * 24)


def seed(email, username, name, bio, socials, appearance, links, views):
    """links: (url, title, tags, on_profile, alias, (min_clicks, max_clicks))"""
    uid = r.users.create_user(email, "demo12345", username)
    r.users.update_profile(uid, name, bio)
    r.users.set_socials(uid, socials)
    r.users.set_appearance(uid, appearance)
    for url, title, tags, on_profile, alias, clicks in links:
        code = alias or "".join(random.choices("abcdefghjkmnpqrstuvwxyz23456789", k=6))
        lid = r.links.create_link(uid, url, code, alias, title=title, tags=tags, on_profile=on_profile)
        n = random.randint(*clicks)
        db.analytics.insert_many([{
            "type": "click", "user_id": ObjectId(uid), "link_id": ObjectId(lid), "timestamp": recent(),
            "source": random.choices(["bio", "direct", "qr"], [5, 4, 1])[0] if on_profile else random.choice(["direct", "qr"]),
            "country": random.choices(countries, [8, 6, 3, 3, 2, 2, 1, 1])[0], "city": None,
            "device": random.choices(["Mobile", "Desktop", "Tablet"], [6, 3, 1])[0],
            "browser": random.choice(["Chrome", "Safari", "Mobile Safari", "Firefox", "Edge"]),
            "os": random.choice(["iOS", "Android", "Mac OS X", "Windows"]),
            "referrer": random.choice(refs),
        } for _ in range(n)])
        db.links.update_one({"_id": ObjectId(lid)}, {"$set": {"clicks": n}})
    db.analytics.insert_many([{
        "type": "profile_view", "user_id": ObjectId(uid), "link_id": None, "timestamp": recent(),
        "source": "direct", "country": random.choice(countries), "city": None, "device": "Mobile",
        "browser": "Safari", "os": "iOS", "referrer": "instagram.com",
    } for _ in range(views)])


seed(
    "demo@shrinkk.app", "bishal", "Bishal",
    "Product designer & creator. Sharing tools, templates and what I'm building ✨",
    {"instagram": "@bishal", "x": "@bishal", "youtube": "@bishal", "github": "bishal", "website": "bishal.design"},
    {"theme": "classic"},
    [
        ("https://bishal.design/portfolio", "My portfolio", ["work"], True, "portfolio", (40, 260)),
        ("https://youtube.com/watch?v=dQw4w9WgXcQ", "Latest video: Figma tips", ["video", "social"], True, None, (40, 260)),
        ("https://gumroad.com/bishal/ui-kit", "UI Kit — 40% off this week", ["shop"], True, "uikit", (40, 260)),
        ("https://cal.com/bishal/intro", "Book a 1:1 call", ["work"], True, None, (40, 260)),
        ("https://medium.com/@bishal/design-systems-at-scale-2026", "", ["blog"], False, None, (40, 260)),
        ("https://dribbble.com/shots/19953119-invoice-landing-page", "Dribbble shot", ["social"], False, "shot", (40, 260)),
        ("https://docs.google.com/forms/d/e/1FAIpQLSf/viewform", "Newsletter signup", [], False, None, (40, 260)),
    ],
    views=900,
)
seed(
    "sima@shrinkk.app", "sima", "Sima", "Indie dev. Shipping in public.",
    {"github": "sima", "x": "@sima", "website": "sima.codes"},
    {"theme": "midnight"},
    [
        ("https://sima.substack.com", "My newsletter", ["writing"], True, None, (20, 120)),
        ("https://github.com/sima", "GitHub projects", ["code"], True, None, (20, 120)),
        ("https://cal.com/sima/chat", "Book a call", [], True, None, (20, 120)),
    ],
    views=300,
)
seed(
    "basak@shrinkk.app", "basak", "Basak", "New single out now 🎧",
    {"instagram": "@basakmusic", "tiktok": "@basakmusic", "youtube": "@basakmusic"},
    {"theme": "sunset"},
    [
        ("https://open.spotify.com/artist/basak", "Listen on Spotify", ["music"], True, None, (20, 120)),
        ("https://basakmusic.com/tour", "Tour dates", ["music"], True, None, (20, 120)),
        ("https://basakmusic.com/merch", "Merch", ["shop"], True, None, (20, 120)),
    ],
    views=300,
)

if __name__ == "__main__":
    print(f"Demo running at http://localhost:{PORT}  (log in: demo@shrinkk.app / demo12345)")
    print("Bio pages: /@bishal  /@sima  /@basak")
    app.run(port=PORT, debug=False)
