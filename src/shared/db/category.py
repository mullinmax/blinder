from pydantic import StringConstraints
from typing import List
from flask import current_app
import hashlib

from .base import BlinderBaseModel
from .item import ItemStrict
from typing_extensions import Annotated


class Category(BlinderBaseModel):
    user_hash: str
    name: Annotated[str, StringConstraints(strict=True, min_length=1)]
    name_hash: str = ""  # generated if not provided

    @property
    def __key__(self):
        if not self.name_hash:
            self.name_hash = hashlib.sha256(self.name.encode()).hexdigest()
        return f"USER:{self.user_hash}:CATEGORY:{self.name_hash}"

    def create(self):
        category_key = self.__key__
        with self.redis_con() as r:
            if r.exists(category_key):
                raise Exception(f"Category with name {self.name} already exists")

            r.hset(
                category_key, mapping={"name": self.name, "user_hash": self.user_hash}
            )
            r.sadd(f"USER:{self.user_hash}:CATEGORIES", self.name_hash)

        return category_key

    @classmethod
    def read(cls, user_hash, name_hash):
        with cls.redis_con() as r:
            category_data = r.hgetall(f"USER:{user_hash}:CATEGORY:{name_hash}")
            current_app.logger.info(category_data)

        if category_data:
            return Category(**category_data, name_hash=name_hash)
        else:
            raise Exception("Category does not exist")

    @classmethod
    def read_all(cls, user_hash) -> List["Category"]:
        with cls.redis_con() as r:
            category_name_hashs = r.smembers(f"USER:{user_hash}:CATEGORIES")

        categories = []
        for name_hash in category_name_hashs:
            categories.append(cls.read(user_hash, name_hash))
        return categories

    def get_all_items(self):
        current_app.logger.info(f"getting all items in {self.__key__}")

        with self.redis_con() as r:
            url_hashes = r.zrange(f"{self.__key__}:ITEMS", 0, -1)

        current_app.logger.info(f"retreived {len(url_hashes)} url_hashes")
        items = [ItemStrict.read(url_hash) for url_hash in url_hashes]
        items = [i for i in items if i]
        current_app.logger.info(f"number of items retreived: {len(items)}")
        if len(items) > 0:
            current_app.logger.info(f"First item: {str(items[0])}")
        return items
