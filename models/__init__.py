from dataclasses import dataclass

from models.analytics_model import AnalyticsModel
from models.link_model import LinkModel
from models.media_model import MediaModel
from models.user_model import UserModel


@dataclass
class Repos:
    users: UserModel
    links: LinkModel
    events: AnalyticsModel
    media: MediaModel

    @classmethod
    def from_db(cls, db):
        return cls(
            users=UserModel(db),
            links=LinkModel(db),
            events=AnalyticsModel(db),
            media=MediaModel(db),
        )

    def ensure_indexes(self):
        self.users.ensure_indexes()
        self.links.ensure_indexes()
        self.events.ensure_indexes()
