import datetime
from abc import ABC, abstractmethod
from uuid import UUID

import redis


# YAGNI
class AbstractStorage(ABC):
    @abstractmethod
    def set_token(self, user_id: UUID, device_id: str, token_id: str, expires_at: int):
        """устанавливаем токен как валидный"""

    @abstractmethod
    def check_token(self, user_id: UUID, device_id: str, token_id: str):
        """проверяем токен на валидность"""

    @abstractmethod
    def exist_token(self, user_id: UUID, device_id: str) -> bool:
        """key exists"""

    @abstractmethod
    def remove_token(self, user_id: UUID, device_id: str):
        """удаляем токен пользователя"""

    @abstractmethod
    def set_payload(self, user_id: UUID, payload: str, ttl: int):
        pass

    @abstractmethod
    def get_payload(self, user_id: UUID) -> str | None:
        pass

    @abstractmethod
    def remove_payload(self, user_id: UUID):
        pass

    @abstractmethod
    def get_devices(self, user_id: UUID) -> list[str | None]:
        pass

    @abstractmethod
    def add_device(self, user_id: UUID, device_id: str):
        pass

    @abstractmethod
    def remove_device(self, user_id: UUID, device_id: str):
        pass

    @abstractmethod
    def set_info(self, user_id: UUID, device_id: str, data: dict, ttl: int):
        """сохраняем информацию о сессии"""

    @abstractmethod
    def delete_info(self, user_id: UUID, device_id: str):
        """удаляем информацию о сессии"""

    @abstractmethod
    def get_info(self, user_id: UUID, device_id: str) -> dict:
        """получаем информацию о сессии"""
        pass


class Storage(AbstractStorage):
    """Быстрое хранилище для ключей - типа Редис"""

    redis: redis.Redis

    def __init__(self, redis_uri):
        self.redis = redis.from_url(redis_uri)

    @staticmethod
    def token_key(user_id: UUID, device_id: str) -> str:
        return f"user:{user_id}:device:{device_id}"

    @staticmethod
    def payload_key(user_id: UUID) -> str:
        return f"user:{user_id}:payload"

    @staticmethod
    def devices_key(user_id: UUID) -> str:
        return f"user:{user_id}:devices"

    @staticmethod
    def info_key(user_id: UUID, device_id: str) -> str:
        return f"user:{user_id}:device:{device_id}:info"

    def set_token(self, user_id: UUID, device_id: str, token_id: str, expires_at: int):
        key = self.token_key(user_id, device_id)
        self.redis.set(name=key, value=token_id, exat=expires_at)

    def check_token(self, user_id: UUID, device_id: str, token_id: str) -> bool:
        key = self.token_key(user_id, device_id)
        value = self.redis.get(key)
        result = value and (value.decode("utf-8") == token_id)
        return result

    def exist_token(self, user_id: UUID, device_id: str) -> bool:
        """key exists"""
        key = self.token_key(user_id, device_id)
        return self.redis.exists(key) > 0

    def remove_token(self, user_id: UUID, device_id: str):
        key = self.token_key(user_id, device_id)
        self.redis.delete(key)

    def set_payload(self, user_id: UUID, payload: str, ttl: int):
        key = self.payload_key(user_id)
        self.redis.set(name=key, value=payload, ex=ttl)

    def get_payload(self, user_id: UUID) -> str | None:
        key = self.payload_key(user_id)
        result = self.redis.get(name=key)
        return result

    def remove_payload(self, user_id: UUID):
        key = self.payload_key(user_id)
        self.redis.delete(key)

    def get_devices(self, user_id: UUID) -> list[str]:
        key = self.devices_key(user_id)
        result = self.redis.smembers(name=key)
        result = [device.decode("utf-8") for device in result]
        return result

    def add_device(self, user_id: UUID, device_id: str):
        key = self.devices_key(user_id)
        self.redis.sadd(key, device_id)

    def remove_device(self, user_id: UUID, device_id: str):
        key = self.devices_key(user_id)
        self.redis.srem(key, device_id)

    def set_info(self, user_id: UUID, device_id: str, data: dict, ttl: int):
        key = self.info_key(user_id, device_id)
        # всегда сохраняем время последней активности
        active_at = str(datetime.datetime.now())
        self.redis.hset(key, "active_at", active_at, data)

        self.redis.expire(key, ttl)

    def delete_info(self, user_id: UUID, device_id: str):
        key = self.info_key(user_id, device_id)
        self.redis.delete(key)

    def get_info(self, user_id: UUID, device_id: str) -> dict | None:
        key = self.info_key(user_id, device_id)
        data = self.redis.hgetall(key)
        if not data:
            return None

        result = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
        return result
