from http import HTTPStatus
from uuid import UUID

import app.services.auth_service as auth_srv
from app.core.utils import error
from app.db.database import AbstractUsers, User

users: AbstractUsers


def add_user(email: str, password: str, name: str) -> dict:
    # если существует такой пользователь
    if users.is_user_exists(email):
        error("User with this email already registered", HTTPStatus.CONFLICT)

    user = users.add_user(email, password, name)
    # TODO отправить ссылку подтверждения на почту
    # можно давать пользователю роль NEW_USER, выдавать короткий токен и ждать подтверждения почты
    # примерно так: mailer.send_notification(email)
    return user.dict(exclude={"password_hash"})


def change_user(user_id: UUID, new_password: str | None, new_name: str | None) -> dict:
    user: User = users.user_by_id(user_id)
    if user is None:
        error(f"User id {user_id} not found", HTTPStatus.NOT_FOUND)

    user = users.change_user(user_id, new_name, new_password)
    return user.dict(exclude={"password_hash"})


def get_user_by_id(user_id: UUID) -> dict:
    if (user := users.user_by_id(user_id)) is None:
        error(f"User id {user_id} not found", HTTPStatus.NOT_FOUND)
    return user.dict(exclude={"password_hash"})


def get_user_sessions(user_id: UUID) -> list[dict]:
    get_user_by_id(user_id)  # проверка что пользователь существует
    return auth_srv.get_user_sessions(user_id)


def get_user_history(user_id: UUID, days_limit=30) -> list[dict]:
    return auth_srv.get_user_history(user_id, days_limit)


def logout_all(user_id: UUID):
    auth_srv.close_all_user_sessions(user_id)


def get_users_info(user_ids: list[UUID]):
    return [userinfo.dict() for userinfo in users.users_info(user_ids)]
