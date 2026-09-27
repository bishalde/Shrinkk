from datetime import datetime, timezone
from bson import ObjectId


class AnalyticsModel:
    def __init__(self, db):
        self.collection = db.analytics
        try:
            self.collection.create_index("link_id")
        except Exception:
            pass

    def log_click(self, link_id, ip, country, city, device, browser, os, referrer):
        entry = {
            "link_id": ObjectId(link_id),
            "timestamp": datetime.now(timezone.utc),
            "ip": ip,
            "country": country or "Unknown",
            "city": city or "Unknown",
            "device": device or "Unknown",
            "browser": browser or "Unknown",
            "os": os or "Unknown",
            "referrer": referrer or "Direct",
        }
        self.collection.insert_one(entry)

    def get_by_link(self, link_id):
        return list(
            self.collection.find({"link_id": ObjectId(link_id)}).sort("timestamp", -1)
        )

    def get_stats(self, link_id):
        pipeline = [
            {"$match": {"link_id": ObjectId(link_id)}},
            {
                "$facet": {
                    "by_country": [
                        {"$group": {"_id": "$country", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 10},
                    ],
                    "by_device": [
                        {"$group": {"_id": "$device", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                    ],
                    "by_browser": [
                        {"$group": {"_id": "$browser", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                    ],
                    "by_referrer": [
                        {"$group": {"_id": "$referrer", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 10},
                    ],
                    "by_date": [
                        {
                            "$group": {
                                "_id": {
                                    "$dateToString": {
                                        "format": "%Y-%m-%d",
                                        "date": "$timestamp",
                                    }
                                },
                                "count": {"$sum": 1},
                            }
                        },
                        {"$sort": {"_id": 1}},
                        {"$limit": 30},
                    ],
                    "total": [{"$count": "count"}],
                }
            },
        ]
        result = list(self.collection.aggregate(pipeline))
        if result:
            stats = result[0]
            stats["total"] = stats["total"][0]["count"] if stats["total"] else 0
            return stats
        return {
            "by_country": [],
            "by_device": [],
            "by_browser": [],
            "by_referrer": [],
            "by_date": [],
            "total": 0,
        }
