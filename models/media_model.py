import gridfs
from bson import ObjectId
from bson.errors import InvalidId


class MediaModel:
    """Avatar images stored in GridFS (Vercel functions have no persistent disk)."""

    def __init__(self, db):
        self.fs = gridfs.GridFS(db, collection="media")

    def save(self, data, content_type, user_id):
        file_id = self.fs.put(data, metadata={"content_type": content_type, "user_id": ObjectId(user_id)})
        return str(file_id)

    def get(self, file_id):
        try:
            return self.fs.get(ObjectId(file_id))
        except (InvalidId, TypeError, gridfs.errors.NoFile):
            return None

    def delete(self, file_id):
        if not file_id:
            return
        try:
            self.fs.delete(ObjectId(file_id))
        except (InvalidId, TypeError):
            pass
