from datetime import datetime, timedelta, timezone

from bson import ObjectId

CLICK = "click"
PROFILE_VIEW = "profile_view"


def _day_keys(days):
    today = datetime.now(timezone.utc).date()
    return [(today - timedelta(days=offset)).isoformat() for offset in range(days - 1, -1, -1)]


def _since(days):
    start = datetime.now(timezone.utc).date() - timedelta(days=days - 1)
    return datetime(start.year, start.month, start.day, tzinfo=timezone.utc)


class AnalyticsModel:
    """Click and profile-view events. Stored in the legacy `analytics` collection."""

    def __init__(self, db):
        self.collection = db.analytics

    def ensure_indexes(self):
        self.collection.create_index([("link_id", 1), ("timestamp", -1)])
        self.collection.create_index([("user_id", 1), ("type", 1), ("timestamp", -1)])

    def _log(self, event_type, user_id, visitor, link_id=None):
        self.collection.insert_one({
            "type": event_type,
            "user_id": ObjectId(user_id),
            "link_id": ObjectId(link_id) if link_id else None,
            "timestamp": datetime.now(timezone.utc),
            "source": visitor.get("source", "direct"),
            "country": visitor.get("country"),
            "city": visitor.get("city"),
            "device": visitor.get("device"),
            "browser": visitor.get("browser"),
            "os": visitor.get("os"),
            "referrer": visitor.get("referrer"),
        })

    def log_click(self, link, visitor):
        self._log(CLICK, link["user_id"], visitor, link_id=link["_id"])

    def log_profile_view(self, user_id, visitor):
        self._log(PROFILE_VIEW, user_id, visitor)

    # --- aggregation helpers -------------------------------------------------

    def _breakdown(self, match, field, limit=8):
        rows = self.collection.aggregate([
            {"$match": match},
            {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ])
        return [{"label": r["_id"] or "Unknown", "count": r["count"]} for r in rows]

    def _series(self, match, days):
        rows = self.collection.aggregate([
            {"$match": {**match, "timestamp": {"$gte": _since(days)}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "count": {"$sum": 1},
            }},
        ])
        counts = {r["_id"]: r["count"] for r in rows}
        return [{"date": day, "count": counts.get(day, 0)} for day in _day_keys(days)]

    def _count(self, match):
        return self.collection.count_documents(match)

    # --- public stats ----------------------------------------------------------

    def link_stats(self, link_id, days=30):
        match = {"link_id": ObjectId(link_id), "type": {"$ne": PROFILE_VIEW}}
        return {
            "total": self._count(match),
            "series": self._series(match, days),
            "by_country": self._breakdown(match, "country"),
            "by_device": self._breakdown(match, "device"),
            "by_browser": self._breakdown(match, "browser"),
            "by_os": self._breakdown(match, "os"),
            "by_referrer": self._breakdown(match, "referrer"),
            "by_source": self._breakdown(match, "source"),
        }

    def account_stats(self, user_id, days=30):
        owner = ObjectId(user_id)
        clicks = {"user_id": owner, "type": CLICK}
        views = {"user_id": owner, "type": PROFILE_VIEW}
        since = {"timestamp": {"$gte": _since(days)}}
        clicks_in_range = {**clicks, **since}
        views_in_range = {**views, **since}
        bio_clicks = self._count({**clicks_in_range, "source": "bio"})
        profile_views = self._count(views_in_range)
        return {
            "days": days,
            "clicks": self._count(clicks_in_range),
            "profile_views": profile_views,
            "bio_clicks": bio_clicks,
            "bio_ctr": round(bio_clicks / profile_views * 100, 1) if profile_views else 0,
            "click_series": self._series(clicks, days),
            "view_series": self._series(views, days),
            "by_country": self._breakdown(clicks_in_range, "country"),
            "by_device": self._breakdown(clicks_in_range, "device"),
            "by_referrer": self._breakdown(clicks_in_range, "referrer"),
            "by_source": self._breakdown(clicks_in_range, "source"),
            "top_links": self._top_links(clicks_in_range),
        }

    def _top_links(self, match, limit=5):
        rows = self.collection.aggregate([
            {"$match": match},
            {"$group": {"_id": "$link_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ])
        return [{"link_id": str(r["_id"]), "count": r["count"]} for r in rows if r["_id"]]

    # --- cleanup ---------------------------------------------------------------

    def delete_for_links(self, link_ids):
        self.collection.delete_many({"link_id": {"$in": [ObjectId(i) for i in link_ids]}})

    def delete_for_user(self, user_id):
        self.collection.delete_many({"user_id": ObjectId(user_id)})

    def backfill_legacy(self, links_collection):
        """Give pre-revamp click events a `type` and owner `user_id`. Safe to re-run."""
        updated = 0
        for link in links_collection.find({}, {"user_id": 1}):
            result = self.collection.update_many(
                {"link_id": link["_id"], "user_id": {"$exists": False}},
                {"$set": {"type": CLICK, "user_id": link["user_id"], "source": "direct"},
                 "$unset": {"ip": ""}},
            )
            updated += result.modified_count
        return updated
