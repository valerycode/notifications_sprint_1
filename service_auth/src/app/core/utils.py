import hashlib
import string
from functools import wraps
from http import HTTPStatus
from secrets import choice as secrets_choice
from uuid import UUID

from flask import current_app, request
from flask_jwt_extended import get_jwt, jwt_required
from flask_jwt_extended.exceptions import NoAuthorizationError

from app.core import constants
from app.core.exceptions import AuthServiceError


def device_id_from_name(device_name: str):
    return hashlib.sha256(device_name.encode("utf8")).hexdigest()


def jwt_accept_roles(roles_list: str | list[str]):
    """
    decorator for routers with accepted roles

    :param roles_list - list of accepted roles like ["user","admin"]
                        or string like "user, admin"
    Grant access if roles_list INTERSECT user_roles NOT NULL
    """

    def decorator(f):
        @jwt_required()
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if isinstance(roles_list, str):
                accepted_roles = list(map(str.strip, roles_list.split(",")))
            else:
                accepted_roles = roles_list

            token = get_jwt()
            roles = token.get("roles", [])
            # if superuser - dont check roles
            if constants.ROOT_ROLE not in roles:
                roles_intersect = set(accepted_roles) & set(roles)
                if not roles_intersect:
                    raise NoAuthorizationError(f"Only roles {accepted_roles} accepted")

            rv = f(*args, **kwargs)
            return rv

        return decorated_function

    return decorator


def secret_key_required(secret_key: str):
    """
    Требует secret_key в заголовках Authorization
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            nonlocal secret_key
            if secret_key is None:
                secret_key = current_app.secret_key

            header_secret_key = request.headers.get('Authorization', '')
            if header_secret_key != secret_key:
                raise NoAuthorizationError(f"Invalid secret key")

            rv = f(*args, **kwargs)
            return rv
        return decorated_function
    return decorator


def validate_uuids(*args: str) -> None:
    for id_ in args:
        try:
            UUID(str(id_))
        except ValueError:
            raise AuthServiceError(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=f"Invalid UUID value {id_}")


def error(msg: str, code: int) -> None:
    """
    :param msg: error message
    :param code: HTTP status Code
    :return: None
        raise HTTPError, which must be caught by Flask error handler
    """
    raise AuthServiceError(status_code=code, detail=msg)


def limit_by_user_id_key() -> str:
    user_id = get_jwt()["sub"]
    return f"limit:{user_id}"


def limit_by_ip_key() -> str:
    if (ip := request.headers.get("X-Real-IP")) is None:  # check if request proxied by nginx
        ip = request.remote_addr
    return f"limit:{ip}"


def require_header_request_id():
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        # если режим debug и Request-Id нет, разрешаем так заходить
        if current_app.debug:
            pass
        else:
            error("X-Request-Id header id is required", HTTPStatus.BAD_REQUEST)


def generate_password(length=10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets_choice(alphabet) for _ in range(length))
