from datetime import timedelta
from http import HTTPStatus

import pytest
from freezegun import freeze_time


@pytest.fixture
def example_user_login_response(client):
    response = client.post("auth/v1/login", json={"email": "example", "password": "example"})
    return response


@pytest.fixture
def example_user_tokens(example_user_login_response, client):
    cookies = {cookie.name: cookie.value for cookie in client.cookie_jar}
    access_token = example_user_login_response.json["access_token"]
    refresh_token = cookies.get("refresh_token_cookie")
    csrf_refresh = cookies.get("csrf_refresh_token")
    return access_token, refresh_token, csrf_refresh


def test_login(example_user_login_response):
    response = example_user_login_response
    assert response.status_code == HTTPStatus.OK
    assert "access_token" in response.json
    assert "refresh_token" in response.json
    assert "refresh_token_cookie" in response.headers.get("Set-Cookie")
    assert "HttpOnly" in response.headers.get("Set-Cookie")
    assert "Path=/auth/v1/refresh" in response.headers.get("Set-Cookie")


@pytest.mark.parametrize(
    "query, status_code",
    [
        ({"email": "not email", "password": "test"}, HTTPStatus.UNAUTHORIZED),
        ({"email": "test", "password": "invalid"}, HTTPStatus.UNAUTHORIZED),
        ({"invalid_key": "test", "password": "test"}, HTTPStatus.BAD_REQUEST),
        ({"email": "test"}, HTTPStatus.BAD_REQUEST),
        ({"password": "test"}, HTTPStatus.BAD_REQUEST),
        ({"invalid_key": "test", "password": "test", "excess_key": "value"}, HTTPStatus.BAD_REQUEST),
    ],
)
def test_login_errors(query, status_code, client):
    response = client.post("auth/v1/login", json=query)
    assert response.status_code == status_code


def test_refresh(client, example_user_tokens):
    _, refresh_token, csrf_token = example_user_tokens
    client.set_cookie("localhost", "refresh_token_cookie", refresh_token)
    response = client.post("auth/v1/refresh", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == HTTPStatus.OK
    assert "access_token" in response.json
    assert "refresh_token" in response.json
    # assert "refresh_token_cookie" in response.headers.get("Set-Cookie")
    # assert "HttpOnly" in response.headers.get("Set-Cookie")
    # assert "Path=auth/v1/refresh" in response.headers.get("Set-Cookie")


def test_refresh_token_expire(client, example_user_tokens):
    _, refresh_token, csrf_token = example_user_tokens
    client.set_cookie("localhost", "refresh_token_cookie", refresh_token)
    with freeze_time(timedelta(days=30, seconds=1)):
        response = client.post("auth/v1/refresh", headers={"X-CSRF-TOKEN": csrf_token})
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json["msg"] == "Token has expired"


# TODO добавить токены с неправильной подписью
@pytest.mark.parametrize(
    "test_refresh, test_csrf, status_code",
    [
        (None, "valid_token", HTTPStatus.UNAUTHORIZED),
        ("invalid_token", "valid_token", HTTPStatus.UNPROCESSABLE_ENTITY),
        ("invalid_name", "valid_token", HTTPStatus.UNAUTHORIZED),
        ("valid_token", None, HTTPStatus.UNAUTHORIZED),
        ("valid_token", "invalid_token", HTTPStatus.UNAUTHORIZED),
        ("valid_token", "invalid_name", HTTPStatus.UNAUTHORIZED),
    ],
)
def test_refresh_errors(test_refresh, test_csrf, status_code, client, example_user_tokens):
    _, valid_refresh_token, valid_csrf_token = example_user_tokens
    client.cookie_jar.clear()
    if test_refresh is None:
        pass
    elif test_refresh == "valid_token":
        client.set_cookie("localhost", "refresh_token_cookie", valid_refresh_token)
    elif test_refresh == "invalid_name":
        client.set_cookie("localhost", "invalid_name", valid_refresh_token)
    else:
        client.set_cookie("localhost", "refresh_token_cookie", test_refresh)
    if test_csrf is None:
        headers = {}
    elif test_csrf == "valid_token":
        headers = {"X-CSRF-TOKEN": valid_csrf_token}
    elif test_csrf == "invalid_name":
        headers = {"X-INVALID_NAME": valid_csrf_token}
    else:
        headers = {"X-CSRF-TOKEN": test_csrf}

    response = client.post("auth/v1/refresh", headers=headers)
    assert response.status_code == status_code


def test_logout(client, example_user_tokens):
    access_token, refresh_token, csrf_token = example_user_tokens
    response = client.post("auth/v1/logout", headers={"Authorization": "Bearer " + access_token})
    assert response.status_code == HTTPStatus.OK

    client.set_cookie("localhost", "refresh_token_cookie", refresh_token)
    response = client.post("auth/v1/refresh", headers={"X-CSRF-TOKEN": csrf_token})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_access_token_expire(client, example_user_tokens):
    access_token, _, _ = example_user_tokens
    with freeze_time(timedelta(hours=1, seconds=1)):
        response = client.post("auth/v1/logout", headers={"Authorization": "Bearer " + access_token})
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json["msg"] == "Token has expired"


@pytest.mark.parametrize(
    "test_access, status_code",
    [
        (None, HTTPStatus.UNAUTHORIZED),
        ("invalid_token", HTTPStatus.UNPROCESSABLE_ENTITY),
    ],
)
def test_logout_errors(test_access, status_code, client):
    if test_access is None:
        headers = {}
    else:
        headers = {"Authorization": "Bearer " + test_access}

    response = client.post("auth/v1/logout", headers=headers)
    assert response.status_code == status_code
