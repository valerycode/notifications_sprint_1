import json
from http import HTTPStatus
from uuid import UUID

from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

import config
from app.core.utils import device_id_from_name, error
from app.db.database import AbstractUsers, User
from app.db.storage import AbstractStorage

storage: AbstractStorage
users: AbstractUsers


def is_user_active(user_id: UUID) -> bool:
    refresh_devices(user_id)
    return bool(storage.get_devices(user_id))


def set_token_payload(user: User, only_active: bool = False) -> dict | None:
    """создает загрузку токена из User, для унификации
    если only_active - то предварительно проверяет что пользователь активен
    """
    if only_active and not is_user_active(user.id):
        return None
    payload = token_payload_from_user(user)
    storage.set_payload(user.id, json.dumps(payload), ttl=get_auth_token_expires())
    return payload


def token_payload_from_user(user: User) -> dict:
    """User -> {token_payload}"""
    payload = {"name": user.name, "roles": user.roles_list()}
    return payload


def get_token_payload_by_user_id(user_id: UUID, use_cache_first: bool = True) -> dict:
    """user_id -> User -> {token_payload}"""
    payload = {}
    # пытаемся получить данные из хранилища
    if use_cache_first:
        if data := storage.get_payload(user_id):
            payload = json.loads(data)

    # Если их там нет - получаем из базы
    if not payload:
        user = users.user_by_id(user_id)
        payload = set_token_payload(user)
    return payload


def tokenize(refresh_token: str):
    # сохраняем в редис валидный refresh токен с информацией об устройстве, с которого пришел юзер
    token = decode_token(refresh_token)
    user_id = token["sub"]
    device_id = token["device_id"]
    token_id = token["jti"]
    token_expires_at = token["exp"]
    storage.set_token(user_id, device_id, token_id, token_expires_at)


def new_tokens(user: User, device_name: str) -> tuple[str, str]:
    """Создаем новые токены при входе"""
    device_id = device_id_from_name(device_name)
    payload = set_token_payload(user)
    ext_claims = payload | {"device_id": device_id}

    refresh_token = create_refresh_token(identity=user.id, additional_claims=ext_claims)
    access_token = create_access_token(identity=user.id, additional_claims=ext_claims, fresh=True)
    tokenize(refresh_token)
    storage.add_device(user.id, device_id)

    return access_token, refresh_token


def refresh_tokens(user_id: UUID, device_id: str, old_token_id: str) -> tuple[str, str]:
    """Создаем новые токены"""

    if not storage.check_token(user_id, device_id, old_token_id):
        error("Invalid refresh token", HTTPStatus.UNAUTHORIZED)

    payload = get_token_payload_by_user_id(user_id)
    ext_claims = payload | {"device_id": device_id}

    refresh_token = create_refresh_token(identity=user_id, additional_claims=ext_claims)
    access_token = create_access_token(identity=user_id, additional_claims=ext_claims)
    tokenize(refresh_token)

    return access_token, refresh_token


def remove_token(user_id: UUID, device_id: str):
    """стираем сессию в хранилище"""
    storage.remove_token(user_id, device_id)
    storage.remove_device(user_id, device_id)


def refresh_devices(user_id: UUID) -> list[str]:
    """
    убираем устройства для которых отсутствует запись с токеном
    возвращает список удаленных устройств

    """
    devices = storage.get_devices(user_id)
    if not devices:
        return []

    closed = []

    for device_id in devices:
        if not storage.exist_token(user_id, device_id):
            closed += [device_id]

    for device_id in closed:
        storage.remove_device(user_id, device_id)
    return closed


def get_devices(user_id: UUID) -> list[str]:
    return storage.get_devices(user_id)


def is_valid_device(device_name: str, token_payload: dict):
    """Сверяет хэш имени устройства и device_id в токене"""
    device_id = device_id_from_name(device_name)
    return device_id == token_payload.get("device_id")


def check_token(user_id: UUID, device_id: str, token_id: str):
    """Проверяем не отозван ли refresh токен"""
    return storage.check_token(user_id, device_id, token_id)


def get_refresh_token_expires() -> int:
    """return time of life refresh_token"""
    return config.flask_config.JWT_REFRESH_TOKEN_EXPIRES


def get_auth_token_expires() -> int:
    """return time of life refresh_token"""
    return config.flask_config.JWT_ACCESS_TOKEN_EXPIRES


def set_payload(user_id: UUID, new_payload: dict):
    storage.set_payload(user_id, json.dumps(new_payload))
