from pydantic import StringConstraints
from typing import List, Optional
from typing_extensions import Annotated

from .item_collection import ItemCollection
from .source import Source


# TODO write unit test that ensures we are using hashes where we should be
# (ie. user_hash, name_hash, etc. should be so many characters and of a certain set)
class Feed(ItemCollection):
    user_hash: str
    name: Annotated[str, StringConstraints(strict=True, min_length=1)]

    @property
    def key(self):
        return f"USER:{self.user_hash}:FEED:{self.name_hash}"

    @property
    def sources_key(self):
        return f"{self.key}:SOURCES"

    @property
    def name_hash(self):
        return self.__insecure_hash__(self.name)

    @property
    def source_hashes(self):
        with self.db_con() as r:
            return list(r.smembers(self.sources_key))

    @property
    def sources(self) -> List[Source]:
        return [
            Source.read(
                user_hash=self.user_hash,
                feed_hash=self.name_hash,
                source_hash=source_hash,
            )
            for source_hash in self.source_hashes
        ]

    @property
    def items_key(self):
        return f"{self.key}:ITEMS"

    def create(self):
        with self.db_con() as r:
            if self.exists():
                raise Exception(f"Feed with name {self.name} already exists")

            r.hset(self.key, mapping={"name": self.name})
            r.sadd(f"USER:{self.user_hash}:FEEDS", self.name_hash)

        return self.key

    def delete(self):
        with self.db_con() as r:
            # remove feed from list of user's feeds
            r.srem(f"USER:{self.user_hash}:FEEDS", self.name_hash)

            # delete each source then remove list
            for source_hash in self.source_hashes:
                try:
                    source = Source.read(
                        user_hash=self.user_hash,
                        feed_hash=self.name_hash,
                        source_hash=source_hash,
                    )
                    source.delete()
                except ValueError:
                    # source does not exist
                    pass
            r.delete(self.sources_key)

            # delete list of feed items
            r.delete(f"{self.key}:ITEMS")

            # delete self
            r.delete(self.key)

    @classmethod
    def read(cls, user_hash, name_hash) -> Optional["Feed"]:
        key = f"USER:{user_hash}:FEED:{name_hash}"
        with cls.db_con() as r:
            feed_data = r.hgetall(key)

        if feed_data:
            feed_data["name_hash"] = name_hash
            feed_data["user_hash"] = user_hash
            return Feed(**feed_data)

        return None

    @classmethod
    def read_all(cls, user_hash) -> List["Feed"]:
        with cls.db_con() as r:
            feed_name_hashs = r.smembers(f"USER:{user_hash}:FEEDS")

        feeds = []
        for name_hash in feed_name_hashs:
            feeds.append(cls.read(user_hash=user_hash, name_hash=name_hash))

        return feeds

    def add_source(self, source: Source):
        with self.db_con() as r:
            source.user_hash = self.user_hash
            source.feed_hash = self.name_hash
            if not source.exists():
                source.create()
            r.sadd(f"{self.key}:SOURCES", source.name_hash)

    def delete_source(self, source: Source):
        with self.db_con() as r:
            source.delete()
            r.srem(f"{self.key}:SOURCES", source.name_hash)
