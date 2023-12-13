from http import HTTPStatus
from uuid import UUID

from app.core.utils import error
from app.db.database import AbstractRoles, AbstractUsers, Role

roles: AbstractRoles
users: AbstractUsers


def _error_role_not_found(role_id: UUID):
    """DRY error msg for ROLE NOT FOUND"""
    error(f"Role id {role_id} not found", HTTPStatus.NOT_FOUND)


def _error_user_not_found(user_id: UUID):
    """DRY error msg for USER NOT FOUND"""
    error(f"Role id {user_id} not found", HTTPStatus.NOT_FOUND)


def get_all_roles():
    roles_list = roles.get_all_roles()
    result = [role.dict() for role in roles_list]
    return result


def get_role_by_name(name: str) -> dict | None:
    role = roles.get_role_by_name(name)
    if not role:
        return None

    return role.dict()


def add_role(name: str) -> dict:
    if roles.is_role_exists(name):
        error(f"Role name {name} already exists", HTTPStatus.CONFLICT)

    new_role: Role = roles.add_role(name)
    return new_role.dict()


def delete_role(role_id: UUID):
    if roles.role_by_id(role_id) is None:
        _error_role_not_found(role_id)
    roles.delete_role(role_id)


def update_role(role_id: UUID, new_name: str):
    if roles.role_by_id(role_id) is None:
        _error_role_not_found(role_id)
    roles.update_role(role_id, new_name)


def get_role(role_id: UUID):
    if (role := roles.role_by_id(role_id)) is None:
        _error_role_not_found(role_id)
    return role.dict()


def get_user_roles(user_id: UUID):
    if users.user_by_id(user_id) is None:
        _error_user_not_found(user_id)

    roles_list = roles.get_user_roles(user_id)
    result = [role.dict() for role in roles_list]
    return result


def add_user_role(user_id: UUID, role_id: UUID):
    if users.user_by_id(user_id) is None:
        _error_user_not_found(user_id)
    if roles.role_by_id(role_id) is None:
        _error_role_not_found(role_id)

    roles_list = roles.add_user_role(user_id, role_id)
    result = [role.dict() for role in roles_list]
    return result


def delete_user_role(user_id: UUID, role_id: UUID):
    if users.user_by_id(user_id) is None:
        _error_user_not_found(user_id)
    if roles.role_by_id(role_id) is None:
        _error_role_not_found(role_id)

    roles_list = roles.delete_user_role(user_id, role_id)
    result = [role.dict() for role in roles_list]
    return result
