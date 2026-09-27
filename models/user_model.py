from datetime import datetime, timezone
import bcrypt
from bson import ObjectId


class UserModel:
    def __init__(self, db):
        self.collection = db.users
        try:
            self.collection.create_index("email", unique=True)
        except Exception:
            pass  # Index will be created on first successful connection

    def create_user(self, email, password):
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user = {
            "email": email.lower().strip(),
            "password": hashed,
            "created_at": datetime.now(timezone.utc),
        }
        result = self.collection.insert_one(user)
        return str(result.inserted_id)

    def find_by_email(self, email):
        return self.collection.find_one({"email": email.lower().strip()})

    def find_by_id(self, user_id):
        return self.collection.find_one({"_id": ObjectId(user_id)})

    def verify_password(self, stored_hash, password):
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash)
