import docker
import pytest
import redis
from contextlib import contextmanager
import time
import warnings

from src.shared.config import config
from src.shared.db.base import db_init

# fixtures
from fixtures.category import unique_category  # noqa
from fixtures.item import unique_item_strict  # noqa
from fixtures.feed import unique_feed  # noqa
from fixtures.user import unique_user  # noqa
from src.shared.db.base import db_init  # noqa

client = docker.from_env()


# removes unimportant issue about item urls being strings when serialized
warnings.filterwarnings("ignore", message=".*")


@contextmanager
def redis_container():
    """Context manager to start and stop a Redis Docker container."""
    container_name = "test_redis"

    # Attempt to remove an existing container with the same name
    try:
        old_container = client.containers.get(container_name)
        old_container.remove(force=True)  # Force removal in case it's running
    except docker.errors.NotFound:
        pass  # No existing container to remove

    # Start a new Redis container
    container = client.containers.run(
        "redis:latest",
        name=container_name,
        detach=True,
        auto_remove=True,
        network=config.get("PYTEST_REDIS_DOCKER_NETWORK"),
    )

    yield container_name  # Container name used as the hostname

    # Cleanup: Attempt to stop and remove the container if it still exists
    try:
        container.stop()
    except docker.errors.NotFound:
        pass  # Container already removed


def is_redis_ready(host, port=6379):
    """Check if Redis is ready to accept connections."""
    try:
        r = redis.Redis(host=host, port=port, decode_responses=True)
        r.ping()
        return True
    except redis.ConnectionError:
        return False


def wait_for_redis_to_be_ready(host, timeout=10):
    """Wait for Redis to be ready, up to a specified timeout."""
    for i in range(timeout):
        if is_redis_ready(host):
            return
        time.sleep(1)
    raise RuntimeError("Timed out waiting for Redis to be ready")


@pytest.fixture(scope="session", autouse=True)
def redis_server():
    if config.get("PYTEST_RUNTIME_TYPE", "local") == "local":
        with redis_container() as redis_hostname:
            wait_for_redis_to_be_ready(redis_hostname)
            config.set("REDIS_PORT", 6379)
            config.set("REDIS_HOST", redis_hostname)
            db_init(flush=True)
            yield redis_hostname
    else:
        # In CI/CD environments, assume Redis is already running and configured
        redis_host = config.get("REDIS_HOST")
        wait_for_redis_to_be_ready(redis_host, timeout=60)
        db_init(flush=True)
        yield redis_host
