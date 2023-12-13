import datetime
from http import HTTPStatus
from uuid import UUID

from app.core.utils import device_id_from_name, error
from app.db.database import AbstractActions, AbstractUsers, User
from app.db.storage import AbstractStorage
from app.services.token_service import get_devices, refresh_devices, remove_token

storage: AbstractStorage
users: AbstractUsers
actions: AbstractActions


def auth(email: str, password: str) -> User | None:
    """check user auth and return user if OK"""
    user = users.auth_user(email, password)
    if not user:
        error("Error login/password", HTTPStatus.UNAUTHORIZED)

    return user


def add_history(user_id: UUID, device_name: str, action: str):
    actions.add_user_action(user_id, device_name, action)


def get_user_history(user_id: UUID, days_limit=30) -> list[dict]:
    if users.user_by_id(user_id) is None:
        error("User not found", HTTPStatus.NOT_FOUND)
    user_actions = actions.get_user_actions(user_id, days_limit)
    return [action.dict() for action in user_actions]


def new_session(user_id: UUID, device_name: str, remote_ip: str, ttl: int, social_net: str = ""):
    login_at = str(datetime.datetime.now())
    data = {"device_name": device_name, "remote_ip": remote_ip, "login_at": login_at}
    device_id = device_id_from_name(device_name)
    storage.set_info(user_id, device_id, data, ttl)
    if social_net:
        add_history(user_id, device_name, f"login with {social_net}")
    else:
        add_history(user_id, device_name, "login")


def refresh_session(user_id: UUID, device_name: str, remote_ip: str, ttl: int):
    data = {"remote_ip": remote_ip}
    device_id = device_id_from_name(device_name)
    storage.set_info(user_id, device_id, data, ttl)
    add_history(user_id, device_name, "update")


def close_session(user_id: UUID, device_name: str, remote_ip: str):
    device_id = device_id_from_name(device_name)
    storage.delete_info(user_id, device_id)
    remove_token(user_id, device_id)
    add_history(user_id, device_name, "logout")


def update_sessions(user_id: UUID):
    """Обновляем информацию о текущих сессиях"""
    closed_devices = refresh_devices(user_id)
    for device_id in closed_devices:
        storage.delete_info(user_id, device_id)
        add_history(user_id, "", "timeout logout")


def get_user_sessions(user_id: UUID) -> list[dict]:
    """Возвращает список активных сессий пользователя"""
    update_sessions(user_id)

    devices = get_devices(user_id)
    if not devices:
        return []

    sessions = []
    for device_id in devices:
        info = storage.get_info(user_id, device_id)
        sessions += [info]
    return sessions


def close_all_user_sessions(user_id: UUID):
    """Закрывает все сессии пользователя"""
    sessions = get_user_sessions(user_id)
    for session in sessions:
        close_session(user_id, session["device_name"], session["remote_ip"])
