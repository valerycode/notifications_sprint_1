from flask_jwt_extended import create_access_token

from app.core.utils import device_id_from_name
from app.services import role_service, user_service


def create_roles_and_users():
    """Cоздать роли и пользователей для тестирования. Должен быть активен app_context."""
    role_ids = []
    for role_name in ("admin", "subscriber", "user"):
        role = role_service.add_role(role_name)
        role_ids.append(role["id"])

    # example - как только что зарегистрировавшийся пользователь
    user_service.add_user("example", "example", "example")

    # example_with_roles - пользователь с добавленными ролями, в т.ч. admin
    user = user_service.add_user("example_with_roles", "example", "example")
    user_id = user["id"]
    for role_id in role_ids:
        role_service.add_user_role(user_id, role_id)

    # example_admin - пользователь c ролью только admin
    user = user_service.add_user("example_admin", "example", "example")
    user_id = user["id"]
    role_service.add_user_role(user_id, role_ids[0])


def create_access_token_for_user(email):
    """Cоздать access токен. Должен быть активен app_context."""
    user = user_service.users.user_by_login(email)
    device_id = device_id_from_name("device_auth")
    ext_claims = {"name": user.name, "roles": user.roles_list(), "device_id": device_id}
    access_token = create_access_token(identity=user.id, additional_claims=ext_claims, fresh=True)
    return access_token


def get_tokens_by_login_reqest(client, email, password, device):
    """Получить токены путем отправки запроса на auth/v1/login"""
    response = client.post("auth/v1/login", json={"email": email, "password": password}, headers={"User-Agent": device})
    cookies = {cookie.name: cookie.value for cookie in client.cookie_jar}
    access_token = response.json["access_token"]
    refresh_token = cookies.get("refresh_token_cookie")
    csrf_refresh = cookies.get("csrf_refresh_token")
    return access_token, refresh_token, csrf_refresh
