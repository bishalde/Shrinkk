from datetime import datetime, timezone

import bcrypt
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

PROFILE_FIELDS = ("display_name", "bio")


def _oid(value):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


class UsernameTaken(Exception):
    pass


class UserModel:
    def __init__(self, db):
        self.collection = db.users

    def ensure_indexes(self):
        self.collection.create_index("email", unique=True)
        # Sparse: legacy accounts have no username until they finish onboarding.
        self.collection.create_index("username", unique=True, sparse=True)

    def create_user(self, email, password, username=None):
        user = {
            "email": email.lower().strip(),
            "password": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()),
            "display_name": username or "",
            "bio": "",
            "socials": {},
            "appearance": {},
            "avatar_id": None,
            "created_at": datetime.now(timezone.utc),
        }
        if username:
            user["username"] = username
        return str(self.collection.insert_one(user).inserted_id)

    def find_by_email(self, email):
        return self.collection.find_one({"email": (email or "").lower().strip()})

    def find_by_id(self, user_id):
        oid = _oid(user_id)
        return self.collection.find_one({"_id": oid}) if oid else None

    def find_by_username(self, username):
        return self.collection.find_one({"username": username})

    def username_available(self, username, exclude_user_id=None):
        query = {"username": username}
        if exclude_user_id:
            query["_id"] = {"$ne": ObjectId(exclude_user_id)}
        return self.collection.count_documents(query, limit=1) == 0

    def email_available(self, email, exclude_user_id=None):
        query = {"email": email.lower().strip()}
        if exclude_user_id:
            query["_id"] = {"$ne": ObjectId(exclude_user_id)}
        return self.collection.count_documents(query, limit=1) == 0

    def verify_password(self, stored_hash, password):
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash)

    def _set(self, user_id, fields):
        try:
            self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": fields})
        except DuplicateKeyError as exc:
            raise UsernameTaken() from exc

    def set_username(self, user_id, username):
        self._set(user_id, {"username": username})

    def set_email(self, user_id, email):
        self._set(user_id, {"email": email.lower().strip()})

    def set_password(self, user_id, password):
        self._set(user_id, {"password": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())})

    def update_profile(self, user_id, display_name, bio):
        self._set(user_id, {"display_name": display_name, "bio": bio})

    def set_socials(self, user_id, socials):
        self._set(user_id, {"socials": socials})

    def set_appearance(self, user_id, appearance):
        self._set(user_id, {"appearance": appearance})

    def set_avatar(self, user_id, avatar_id):
        self._set(user_id, {"avatar_id": avatar_id})

    def delete(self, user_id):
        self.collection.delete_one({"_id": ObjectId(user_id)})

    def count(self):
        return self.collection.estimated_document_count()
