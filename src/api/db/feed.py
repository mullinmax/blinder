from pydantic import StringConstraints, HttpUrl
from typing_extensions import Annotated
from datetime import datetime

from constants import FEEDS_TO_INGEST_KEY, FEED_READ_INTERVAL_TIMEDELTA
from .item_collection import ItemCollection


class Feed(ItemCollection):
    user_hash: str
    category_hash: str
    name: Annotated[str, StringConstraints(strict=True, min_length=1)]
    url: HttpUrl

    @property
    def name_hash(self):
        return self.__insecure_hash__(self.name)

    @property
    def key(self):
        return (
            f"USER:{self.user_hash}:CATEGORY:{self.category_hash}:FEED:{self.name_hash}"
        )

    @property
    def items_key(self):
        return f"{self.key}:ITEMS"

    def create(self):
        with self.db_con() as r:
            if r.exists(self.key):
                raise Exception(f"Cannot create duplicate feed {self.key}")

            r.hset(self.key, mapping={"url": str(self.url), "name": self.name})
            self.trigger_ingest(now=True)
        return

    def delete(self):
        with self.db_con() as r:
            r.delete(self.key)
            r.delete(self.items_key)

    def trigger_ingest(self, now=False):
        # if the feed is not already in the list
        # we're assuming it's over due to ingest
        if now:
            score = int(datetime.now().timestamp())
        else:
            score = datetime.now() + FEED_READ_INTERVAL_TIMEDELTA
            score = int((score).timestamp())

        with self.db_con() as r:
            # lt=True means that if the feed is already in the list
            # it will only be updated if the new score is lower
            r.zadd(FEEDS_TO_INGEST_KEY, mapping={self.key: score}, lt=True)

    @classmethod
    def read(cls, user_hash, category_hash, feed_hash):
        feed_key = f"USER:{user_hash}:CATEGORY:{category_hash}:FEED:{feed_hash}"
        feed = cls.read_by_key(feed_key)

        if feed:
            return feed

        raise ValueError("Feed not found")

    @classmethod
    def read_by_key(cls, feed_key):
        with cls.db_con() as r:
            if r.exists(feed_key):
                feed_data = r.hgetall(feed_key)
                _, user_hash, _, category_hash, _, feed_hash = feed_key.split(":")
                return Feed(
                    user_hash=user_hash, category_hash=category_hash, **feed_data
                )
        return None
