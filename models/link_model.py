import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId


def _oid(value):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def _oids(values):
    return [oid for oid in (_oid(v) for v in values) if oid]


def _aware(dt):
    return dt.replace(tzinfo=timezone.utc) if dt and dt.tzinfo is None else dt


class LinkModel:
    def __init__(self, db):
        self.collection = db.links

    def ensure_indexes(self):
        self.collection.create_index("short_code", unique=True)
        self.collection.create_index([("user_id", 1), ("created_at", -1)])
        self.collection.create_index([("user_id", 1), ("on_profile", 1), ("profile_order", 1)])

    def create_link(self, user_id, original_url, short_code, custom_alias=None, expires_at=None,
                    title="", tags=None, on_profile=False):
        now = datetime.now(timezone.utc)
        link = {
            "user_id": ObjectId(user_id),
            "original_url": original_url,
            "short_code": short_code,
            "custom_alias": custom_alias,
            "title": title,
            "tags": tags or [],
            "clicks": 0,
            "is_active": True,
            "on_profile": on_profile,
            "profile_order": self._next_profile_order(user_id) if on_profile else 0,
            "qr": {},
            "expires_at": expires_at,
            "created_at": now,
            "updated_at": now,
        }
        return str(self.collection.insert_one(link).inserted_id)

    def _next_profile_order(self, user_id):
        last = self.collection.find_one(
            {"user_id": ObjectId(user_id), "on_profile": True}, sort=[("profile_order", -1)]
        )
        return (last.get("profile_order", 0) + 1) if last else 0

    def find_by_short_code(self, short_code):
        return self.collection.find_one({"short_code": short_code})

    def short_code_taken(self, short_code, exclude_link_id=None):
        query = {"short_code": short_code}
        if exclude_link_id:
            query["_id"] = {"$ne": ObjectId(exclude_link_id)}
        return self.collection.count_documents(query, limit=1) > 0

    def find_by_id(self, link_id):
        oid = _oid(link_id)
        return self.collection.find_one({"_id": oid}) if oid else None

    def find_owned(self, link_id, user_id):
        oid = _oid(link_id)
        if not oid:
            return None
        return self.collection.find_one({"_id": oid, "user_id": ObjectId(user_id)})

    def find_by_user(self, user_id, search=None, tag=None):
        query = {"user_id": ObjectId(user_id)}
        if search:
            pattern = {"$regex": re.escape(search), "$options": "i"}
            query["$or"] = [
                {"original_url": pattern},
                {"short_code": pattern},
                {"title": pattern},
            ]
        if tag:
            query["tags"] = tag
        return list(self.collection.find(query).sort("created_at", -1))

    def top_by_user(self, user_id, limit=5):
        return list(
            self.collection.find({"user_id": ObjectId(user_id)}).sort("clicks", -1).limit(limit)
        )

    def tags_for_user(self, user_id):
        return sorted(t for t in self.collection.distinct("tags", {"user_id": ObjectId(user_id)}) if t)

    def profile_links(self, user_id, public=False):
        query = {"user_id": ObjectId(user_id), "on_profile": True}
        links = list(self.collection.find(query).sort("profile_order", 1))
        if public:
            links = [l for l in links if self.is_available(l)]
        return links

    def update_link(self, link_id, user_id, updates):
        updates = {**updates, "updated_at": datetime.now(timezone.utc)}
        if updates.get("on_profile") is True:
            current = self.find_owned(link_id, user_id)
            if current and not current.get("on_profile"):
                updates["profile_order"] = self._next_profile_order(user_id)
        return self.collection.update_one(
            {"_id": ObjectId(link_id), "user_id": ObjectId(user_id)}, {"$set": updates}
        )

    def bulk_update(self, link_ids, user_id, updates):
        return self.collection.update_many(
            {"_id": {"$in": _oids(link_ids)}, "user_id": ObjectId(user_id)},
            {"$set": {**updates, "updated_at": datetime.now(timezone.utc)}},
        )

    def bulk_add_tag(self, link_ids, user_id, tag):
        return self.collection.update_many(
            {"_id": {"$in": _oids(link_ids)}, "user_id": ObjectId(user_id)},
            {"$addToSet": {"tags": tag}},
        )

    def reorder_profile(self, user_id, ordered_ids):
        for position, oid in enumerate(_oids(ordered_ids)):
            self.collection.update_one(
                {"_id": oid, "user_id": ObjectId(user_id)}, {"$set": {"profile_order": position}}
            )

    def delete_link(self, link_id, user_id):
        return self.collection.delete_one({"_id": ObjectId(link_id), "user_id": ObjectId(user_id)})

    def delete_many(self, link_ids, user_id):
        """Delete the caller's links among `link_ids`; returns the ids actually deleted."""
        query = {"_id": {"$in": _oids(link_ids)}, "user_id": ObjectId(user_id)}
        ids = [doc["_id"] for doc in self.collection.find(query, {"_id": 1})]
        self.collection.delete_many({"_id": {"$in": ids}})
        return [str(i) for i in ids]

    def delete_all_for_user(self, user_id):
        self.collection.delete_many({"user_id": ObjectId(user_id)})

    def increment_clicks(self, link_id):
        self.collection.update_one({"_id": ObjectId(link_id)}, {"$inc": {"clicks": 1}})

    def count(self):
        return self.collection.estimated_document_count()

    def count_by_user(self, user_id):
        return self.collection.count_documents({"user_id": ObjectId(user_id)})

    def total_clicks(self, user_id=None):
        match = {"user_id": ObjectId(user_id)} if user_id else {}
        result = list(self.collection.aggregate([
            {"$match": match},
            {"$group": {"_id": None, "total": {"$sum": "$clicks"}}},
        ]))
        return result[0]["total"] if result else 0

    @staticmethod
    def is_expired(link):
        expires_at = _aware(link.get("expires_at"))
        return bool(expires_at and expires_at < datetime.now(timezone.utc))

    @classmethod
    def is_available(cls, link):
        return link.get("is_active", True) and not cls.is_expired(link)
