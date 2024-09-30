# fixtures
from tests.fixtures.category import unique_category, existing_category  # noqa
from tests.fixtures.item import unique_item_strict, existing_item_strict  # noqa
from tests.fixtures.item_state import unique_item_state, existing_item_state  # noqa
from tests.fixtures.source import unique_source, existing_source  # noqa
from tests.fixtures.user import unique_user, existing_user  # noqa
from tests.fixtures.client import client  # noqa
from tests.fixtures.token import token  # noqa

from db.base import db_init

db_init()
