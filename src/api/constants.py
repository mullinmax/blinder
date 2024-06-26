from config import config
from datetime import timedelta

FEEDS_TO_INGEST_KEY = "FEED-KEYS-TO-INGEST"
FEED_CHECK_INTERVAL_TIMEDELTA = timedelta(
    minutes=config.get("FEED_CHECK_INTERVAL_MINUTES")
)
