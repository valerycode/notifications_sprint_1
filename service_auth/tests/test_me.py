from http import HTTPStatus

import pytest


def test_get_user_me(client, example_user_id, auth_as_user):
    response = client.get("auth/v1/users/me/", headers=auth_as_user)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("login") == "example"
    assert response.json.get("name") == "example"


@pytest.mark.parametrize(
    "headers, status_code",
    [
        ({"Authorization": "Bearer invalid_token"}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"No-auth": "Bearer invalid_token"}, HTTPStatus.UNAUTHORIZED),
    ],
)
def test_get_user_me_errors(headers, status_code, client):
    response = client.get("auth/v1/users/me/", headers=headers)
    assert response.status_code == status_code


def test_add_user_me_with_name(client):
    response = client.post("auth/v1/users/me/", json={"email": "email", "password": "password", "name": "name"})
    assert response.status_code == HTTPStatus.CREATED
    assert response.json.get("login") == "email"
    assert response.json.get("name") == "name"


def test_add_user_me_without_name(client):
    response = client.post("auth/v1/users/me/", json={"email": "email", "password": "password"})
    assert response.status_code == HTTPStatus.CREATED
    assert response.json.get("login") == "email"
    assert response.json.get("name") == "email"


@pytest.mark.parametrize(
    "query, status_code",
    [
        ({"email": "example", "password": "password"}, HTTPStatus.CONFLICT),
        ({"email": "email", "password": "password", "excess_key": "value"}, HTTPStatus.CREATED),
        ({"email": "email"}, HTTPStatus.BAD_REQUEST),
        ({"password": "password"}, HTTPStatus.BAD_REQUEST),
        ({"invalid_key": "value"}, HTTPStatus.BAD_REQUEST),
    ],
)
def test_add_user_me_errors(query, status_code, client):
    response = client.post("auth/v1/users/me/", json=query)
    assert response.status_code == status_code


def test_add_user_me_authenticated(client, auth_as_user):
    response = client.post(
        "auth/v1/users/me/", json={"email": "email", "password": "password", "name": "name"}, headers=auth_as_user
    )
    assert response.status_code == HTTPStatus.IM_A_TEAPOT


@pytest.mark.parametrize(
    "query, result",
    [
        ({"password": "new_password", "name": "new_name"}, {"password": "new_password", "name": "new_name"}),
        ({"password": "new_password"}, {"password": "new_password", "name": "example"}),
        ({"name": "new_name"}, {"password": "example", "name": "new_name"}),
    ],
)
def test_patch_user_me(query, result, client, example_user_id, auth_as_user):
    response = client.patch("auth/v1/users/me/", json=query, headers=auth_as_user)
    assert response.status_code == HTTPStatus.OK

    response = client.get("auth/v1/users/me/", headers=auth_as_user)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("name") == result["name"]

    response = client.post("auth/v1/login", json={"email": "example", "password": result["password"]})
    assert response.status_code == HTTPStatus.OK


def test_get_user_me_history(client, example_user_id, auth_as_user):
    client.post("auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_1"})
    client.post("auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_1"})
    client.post("auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_2"})

    response = client.get("auth/v1/users/me/history", headers=auth_as_user)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 3
    for i, device in enumerate(("device_1", "device_1", "device_2")):
        assert response.json[i].get("device_name") == device


def test_get_user_me_sessions(client, example_user_id, auth_as_user):
    client.post("auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_1"})
    client.post("auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_1"})
    response = client.post(
        "auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_2"}
    )
    access_token = response.json.get("access_token")

    response = client.get("auth/v1/users/me/sessions", headers=auth_as_user)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 2
    assert set(session["device_name"] for session in response.json) == {"device_1", "device_2"}

    # разлогиниваемся со второго устройства
    client.post("auth/v1/logout", headers={"Authorization": "Bearer " + access_token})

    response = client.get("auth/v1/users/me/sessions", headers=auth_as_user)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert set(session["device_name"] for session in response.json) == {"device_1"}


def test_delete_user_me_sessions(client, example_user_id, auth_as_user):
    client.post("auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_1"})
    response = client.post(
        "auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_2"}
    )
    access_token = response.json.get("access_token")

    response = client.get("auth/v1/users/me/sessions", headers=auth_as_user)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 2
    assert set(session["device_name"] for session in response.json) == {"device_1", "device_2"}

    # удаляем все сессии
    client.delete("auth/v1/users/me/sessions", headers={"Authorization": "Bearer " + access_token})

    response = client.get("auth/v1/users/me/sessions", headers=auth_as_user)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 0
