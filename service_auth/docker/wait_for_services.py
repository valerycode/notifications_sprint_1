import logging.config
import os

import backoff
from psycopg2 import OperationalError, connect
from redis import Redis, RedisError

PG_URI = os.getenv("PG_AUTH_DSN")
REDIS_URI = os.getenv("REDIS_AUTH_DSN")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": logging.DEBUG,
        "formatter": "default",
        "handlers": ["default"],
    },
}

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def fake_send_email(details: dict):
    logger.debug("Send email")


@backoff.on_predicate(backoff.expo, logger=logger, max_time=300, on_giveup=fake_send_email, max_value=5)
def check_postgres(pg_uri: str) -> bool:
    try:
        with connect(pg_uri) as pg_conn:
            with pg_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
    except OperationalError:
        return False


@backoff.on_predicate(backoff.expo, logger=logger, max_time=300, on_giveup=fake_send_email, max_value=5)
def check_redis(redis_client: Redis) -> bool:
    try:
        return redis_client.ping()
    except RedisError:
        return False


def wait():
    redis_client = Redis.from_url(REDIS_URI)
    check_redis(redis_client)

    check_postgres(PG_URI)


if __name__ == "__main__":
    wait()
