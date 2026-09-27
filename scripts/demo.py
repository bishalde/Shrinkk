"""Run Shrinkk locally with an in-memory database pre-filled with demo data.

    python scripts/demo.py            # http://localhost:8080  (log in: demo@shrinkk.app / demo12345)

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

uid = r.users.create_user("demo@shrinkk.app", "demo12345", "maya")
r.users.update_profile(uid, "Maya Chen", "Product designer & creator. Sharing tools, templates and what I'm building ✨")
r.users.set_socials(uid, {"instagram": "@maya", "x": "@maya", "youtube": "@mayachen", "github": "maya", "website": "maya.design"})
r.users.set_appearance(uid, {"theme": "classic"})

random.seed(7)
links = [
    ("https://maya.design/portfolio", "My portfolio", ["work"], True, "portfolio"),
    ("https://youtube.com/watch?v=dQw4w9WgXcQ", "Latest video: Figma tips", ["video", "social"], True, None),
    ("https://gumroad.com/maya/ui-kit", "UI Kit — 40% off this week", ["shop"], True, "uikit"),
    ("https://cal.com/maya/intro", "Book a 1:1 call", ["work"], True, None),
    ("https://medium.com/@maya/design-systems-at-scale-2026", "", ["blog"], False, None),
    ("https://dribbble.com/shots/19953119-invoice-landing-page", "Dribbble shot", ["social"], False, "shot"),
    ("https://docs.google.com/forms/d/e/1FAIpQLSf/viewform", "Newsletter signup", [], False, None),
]
countries = ["US", "IN", "DE", "GB", "BR", "CA", "FR", "JP"]
refs = [None, "instagram.com", "t.co", "youtube.com", "google.com", "linkedin.com"]
now = datetime.now(timezone.utc)
for url, title, tags, on_profile, alias in links:
    code = alias or "".join(random.choices("abcdefghjkmnpqrstuvwxyz23456789", k=6))
    lid = r.links.create_link(uid, url, code, alias, title=title, tags=tags, on_profile=on_profile)
    n = random.randint(40, 260)
    events = []
    for _ in range(n):
        ts = now - timedelta(days=random.betavariate(1.2, 3) * 60, hours=random.random() * 24)
        events.append({
            "type": "click", "user_id": ObjectId(uid), "link_id": ObjectId(lid), "timestamp": ts,
            "source": random.choices(["bio", "direct", "qr"], [5, 4, 1])[0] if on_profile else random.choice(["direct", "qr"]),
            "country": random.choices(countries, [8, 6, 3, 3, 2, 2, 1, 1])[0], "city": None,
            "device": random.choices(["Mobile", "Desktop", "Tablet"], [6, 3, 1])[0],
            "browser": random.choice(["Chrome", "Safari", "Mobile Safari", "Firefox", "Edge"]),
            "os": random.choice(["iOS", "Android", "Mac OS X", "Windows"]),
            "referrer": random.choice(refs),
        })
    db.analytics.insert_many(events)
    db.links.update_one({"_id": ObjectId(lid)}, {"$set": {"clicks": n}})
views = [{
    "type": "profile_view", "user_id": ObjectId(uid), "link_id": None,
    "timestamp": now - timedelta(days=random.betavariate(1.2, 3) * 60, hours=random.random() * 24),
    "source": "direct", "country": random.choice(countries), "city": None, "device": "Mobile",
    "browser": "Safari", "os": "iOS", "referrer": "instagram.com",
} for _ in range(900)]
db.analytics.insert_many(views)

if __name__ == "__main__":
    print(f"Demo running at http://localhost:{PORT}  (log in: demo@shrinkk.app / demo12345, bio page: /@maya)")
    app.run(port=PORT, debug=False)
