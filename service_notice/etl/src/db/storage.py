import logging
from uuid import UUID

import backoff
import redis
from redis.exceptions import ConnectionError

from core.constants import Mark


class Storage:
    redis: redis.Redis

    @backoff.on_exception(backoff.expo, ConnectionError, max_time=60)
    def __init__(self, uri: str):
        logging.debug("start Redis")
        self.redis = redis.from_url(uri)
        self.redis.ping()

    @staticmethod
    def mark_key(notice_id: UUID, user_id: UUID) -> str:
        """определяет ключ для хранения"""
        return f"notice:{notice_id}:user:{user_id}"

    def mark_processed(self, notice_id: UUID, user_id: UUID, result=Mark.QUEUED, ttl=24 * 60 * 60):
        """Помечаем сообщение для пользователя как обработанное"""
        key = self.mark_key(notice_id, user_id)
        self.redis.set(key, result.value, ex=ttl)
        logging.debug("marked notice:{0} user:{1} mark:{2}".format(notice_id, user_id, result.name))

    def get_mark(self, notice_id: UUID, user_id: UUID) -> Mark | None:
        """Получаем отметку или None если такое сообщение еше не встречалось"""
        key = self.mark_key(notice_id, user_id)
        value = self.redis.get(key)
        if not value:
            return None

        value = int(value.decode("utf-8"))
        return Mark(value)

    def close(self):
        if self.redis:
            self.redis.close()
            logging.debug("close Redis")


db: Storage | None = None


def set_mark(notice_id, user_id, result=Mark.QUEUED, ttl=24 * 60 * 60):
    if db:
        db.mark_processed(notice_id, user_id, result, ttl)


def get_mark(notice_id: UUID, user_id: UUID) -> Mark | None:
    if db:
        return db.get_mark(notice_id, user_id)
    else:
        return None
