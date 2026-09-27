from datetime import datetime, timezone
from bson import ObjectId


class LinkModel:
    def __init__(self, db):
        self.collection = db.links
        try:
            self.collection.create_index("short_code", unique=True)
            self.collection.create_index("user_id")
        except Exception:
            pass

    def create_link(self, user_id, original_url, short_code, custom_alias=None, expires_at=None):
        link = {
            "user_id": ObjectId(user_id),
            "original_url": original_url,
            "short_code": short_code,
            "custom_alias": custom_alias,
            "clicks": 0,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
        }
        result = self.collection.insert_one(link)
        return str(result.inserted_id)

    def find_by_short_code(self, short_code):
        return self.collection.find_one({"short_code": short_code})

    def find_by_user(self, user_id, search=None):
        query = {"user_id": ObjectId(user_id)}
        if search:
            query["$or"] = [
                {"original_url": {"$regex": search, "$options": "i"}},
                {"short_code": {"$regex": search, "$options": "i"}},
                {"custom_alias": {"$regex": search, "$options": "i"}},
            ]
        return list(self.collection.find(query).sort("created_at", -1))

    def find_by_id(self, link_id):
        return self.collection.find_one({"_id": ObjectId(link_id)})

    def increment_clicks(self, link_id):
        self.collection.update_one(
            {"_id": ObjectId(link_id)},
            {"$inc": {"clicks": 1}},
        )

    def update_link(self, link_id, user_id, updates):
        return self.collection.update_one(
            {"_id": ObjectId(link_id), "user_id": ObjectId(user_id)},
            {"$set": updates},
        )

    def delete_link(self, link_id, user_id):
        return self.collection.delete_one(
            {"_id": ObjectId(link_id), "user_id": ObjectId(user_id)}
        )

    def count_by_user(self, user_id):
        return self.collection.count_documents({"user_id": ObjectId(user_id)})

    def is_expired(self, link):
        if link.get("expires_at") and link["expires_at"] < datetime.now(timezone.utc):
            return True
        return False
