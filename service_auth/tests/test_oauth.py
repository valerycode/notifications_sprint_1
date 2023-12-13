from http import HTTPStatus

from flask import redirect, request

import app.services.user_service as user_srv
from app.services.oauth_service import OAuthSignIn, get_user_socials

TEST_LOGIN = "test@test.test"


class TestClientOauth(OAuthSignIn):
    """Мок класс для аутентификации. Никуда не ходит, возвращает всегда одинакового пользователя"""

    def __init__(self):
        self.provider_name = "test"

    def authorize(self):
        return redirect(self.get_callback_url() + "?code=123456")

    def callback(self):
        if "code" not in request.args:
            return None, None, None

        code = request.args["code"]
        if code == "123456":
            user_id = "user_123456"
            user_name = "User Test"
            email = TEST_LOGIN
        else:
            user_id = None
            user_name = None
            email = None

        return user_id, user_name, email


def test_social_login_first_time(module_client):
    """Проверка на первый вход в систему. Должен появиться новый пользователь"""
    response = module_client.get("auth/v1/authorize/test", follow_redirects=True)
    assert len(response.history) == 1, "Один редирект"
    user_data = response.json.get("new_user")

    assert response.status_code == HTTPStatus.OK
    assert user_data.get("login") == TEST_LOGIN
    assert response.json.get("access_token") is not None
    assert response.json.get("refresh_token") is not None


def test_social_login_second_time(module_client):
    """Проверка на второй вход в систему. Пользователь уже есть в системе"""
    response = module_client.get("auth/v1/authorize/test", follow_redirects=True)
    assert len(response.history) == 1
    user_data = response.json.get("new_user")

    assert response.status_code == HTTPStatus.OK
    assert user_data is None
    assert response.json.get("access_token") is not None
    assert response.json.get("refresh_token") is not None


def test_user_socials(module_client):
    """Проверяем что у пользователя есть теперь запись с этой соц сетью"""
    user = user_srv.users.user_by_login(TEST_LOGIN)
    assert user is not None
    assert user.login == TEST_LOGIN
    socials = get_user_socials(user.id)
    assert "test" == socials[0]["social_name"]


def test_not_exist_social_login(module_client):
    """Ответ на несуществующую соц сеть"""
    response = module_client.get("auth/v1/authorize/test1", follow_redirects=True)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_none_user_social_login(module_client):
    """Если пользователь не найден"""
    response = module_client.get("auth/v1/callback/test?code=654321", follow_redirects=True)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
