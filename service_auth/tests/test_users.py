from http import HTTPStatus

import pytest


def test_add_user_with_name(client, auth_as_admin):
    response = client.post(
        "auth/v1/users", json={"email": "email", "password": "password", "name": "name"}, headers=auth_as_admin
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json.get("login") == "email"
    assert response.json.get("name") == "name"


def test_add_user_without_name(client, auth_as_admin):
    response = client.post("auth/v1/users", json={"email": "email", "password": "password"}, headers=auth_as_admin)
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
def test_add_user_errors(query, status_code, client, auth_as_admin):
    response = client.post("auth/v1/users", json=query, headers=auth_as_admin)
    assert response.status_code == status_code


def test_get_user(client, example_user_id, auth_as_admin):
    response = client.get(f"auth/v1/users/{example_user_id}", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("login") == "example"
    assert response.json.get("name") == "example"


@pytest.mark.parametrize(
    "user_id, status_code",
    [
        ("not_uuid", HTTPStatus.UNPROCESSABLE_ENTITY),
        ("7f32cd4a-7981-436d-bba7-78169acbbb5d", HTTPStatus.NOT_FOUND),
    ],
)
def test_get_user_errors(user_id, status_code, client, auth_as_admin):
    response = client.get(f"auth/v1/users/{user_id}", headers=auth_as_admin)
    assert response.status_code == status_code


@pytest.mark.parametrize(
    "query, result",
    [
        ({"password": "new_password", "name": "new_name"}, {"password": "new_password", "name": "new_name"}),
        ({"password": "new_password"}, {"password": "new_password", "name": "example"}),
        ({"name": "new_name"}, {"password": "example", "name": "new_name"}),
    ],
)
def test_patch_user(query, result, client, example_user_id, auth_as_admin):
    response = client.patch(f"auth/v1/users/{example_user_id}", json=query, headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK

    response = client.get(f"auth/v1/users/{example_user_id}", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("name") == result["name"]

    response = client.post("auth/v1/login", json={"email": "example", "password": result["password"]})
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "user_id, query, status_code",
    [
        ("not_uuid", {"password": "new_password"}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ("7f32cd4a-7981-436d-bba7-78169acbbb5d", {"password": "new_password"}, HTTPStatus.NOT_FOUND),
    ],
)
def test_patch_user_errors(user_id, query, status_code, client, auth_as_admin):
    response = client.patch(f"auth/v1/users/{user_id}", json=query, headers=auth_as_admin)
    assert response.status_code == status_code


def test_get_empty_user_history(client, example_user_id, auth_as_admin):
    response = client.get(f"auth/v1/users/{example_user_id}/history", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert response.json == []


def test_get_user_history(client, example_user_id, auth_as_admin):
    client.post("auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_1"})
    client.post("auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_1"})
    client.post("auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_2"})

    response = client.get(f"auth/v1/users/{example_user_id}/history", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 3
    for i, device in enumerate(("device_1", "device_1", "device_2")):
        assert response.json[i].get("device_name") == device


@pytest.mark.parametrize(
    "user_id, status_code",
    [("not_uuid", HTTPStatus.UNPROCESSABLE_ENTITY), ("7f32cd4a-7981-436d-bba7-78169acbbb5d", HTTPStatus.NOT_FOUND)],
)
def test_get_user_history_errors(user_id, status_code, client, auth_as_admin):
    response = client.get(f"auth/v1/users/{user_id}/history", headers=auth_as_admin)
    assert response.status_code == status_code


def test_get_user_sessions(client, example_user_id, auth_as_admin):
    client.post("auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_1"})
    client.post("auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_1"})
    response = client.post(
        "auth/v1/login", json={"email": "example", "password": "example"}, headers={"User-Agent": "device_2"}
    )
    access_token = response.json.get("access_token")

    response = client.get(f"auth/v1/users/{example_user_id}/sessions", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 2
    assert set(session["device_name"] for session in response.json) == {"device_1", "device_2"}

    # разлогиниваемся со второго устройства
    client.post("auth/v1/logout", headers={"Authorization": "Bearer " + access_token})

    response = client.get(f"auth/v1/users/{example_user_id}/sessions", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert set(session["device_name"] for session in response.json) == {"device_1"}


@pytest.mark.parametrize(
    "user_id, status_code",
    [("not_uuid", HTTPStatus.UNPROCESSABLE_ENTITY), ("7f32cd4a-7981-436d-bba7-78169acbbb5d", HTTPStatus.NOT_FOUND)],
)
def test_get_user_sessions_errors(user_id, status_code, client, auth_as_admin):
    response = client.get(f"auth/v1/users/{user_id}/sessions", headers=auth_as_admin)
    assert response.status_code == status_code
