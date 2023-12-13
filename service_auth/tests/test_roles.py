from http import HTTPStatus

import pytest

from app.services import role_service


@pytest.fixture
def user_role_id():
    roles = role_service.get_all_roles()
    role_id = [role["id"] for role in roles if role["name"] == "user"][0]
    return role_id


@pytest.mark.parametrize(
    "headers, status_code",
    [
        ({"Authorization": "Bearer invalid_token"}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"No-auth": "Bearer invalid_token"}, HTTPStatus.UNAUTHORIZED),
    ],
)
def test_get_all_roles_auth_errors(headers, status_code, client):
    response = client.get("auth/v1/roles", headers=headers)
    assert response.status_code == status_code


def test_get_all_roles_admin_required(client, auth_as_user):
    response = client.get("auth/v1/roles", headers=auth_as_user)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_all_roles(client, auth_as_admin):
    response = client.get("auth/v1/roles", headers=auth_as_admin)

    assert response.status_code == HTTPStatus.OK
    for role in response.json:
        assert "id" in role
        assert "name" in role
        assert len(role) == 2

    assert len(response.json) == 3
    assert set(role["name"] for role in response.json) == {"admin", "subscriber", "user"}


def test_create_role(client, auth_as_admin):
    response = client.post("auth/v1/roles", json={"name": "test"}, headers=auth_as_admin)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json.get("name") == "test"

    role_id = response.json.get("id")
    response = client.get(f"auth/v1/roles/{role_id}", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("name") == "test"


@pytest.mark.parametrize(
    "query, status_code",
    [
        ({"name": "admin"}, HTTPStatus.CONFLICT),
        ({"invalid key": "test"}, HTTPStatus.BAD_REQUEST),
        ({"name": "test", "excess_key": "value"}, HTTPStatus.CREATED),
    ],
)
def test_create_role_errors(query, status_code, client, auth_as_admin):
    response = client.post("auth/v1/roles", json=query, headers=auth_as_admin)

    assert response.status_code == status_code


def test_get_role(client, user_role_id, auth_as_admin):
    response = client.get(f"auth/v1/roles/{user_role_id}", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("name") == "user"


@pytest.mark.parametrize(
    "role_id, status_code",
    [
        ("not_uuid", HTTPStatus.UNPROCESSABLE_ENTITY),
        ("7f32cd4a-7981-436d-bba7-78169acbbb5d", HTTPStatus.NOT_FOUND),
    ],
)
def test_get_role_errors(role_id, status_code, client, auth_as_admin):
    response = client.get(f"auth/v1/roles/{role_id}", headers=auth_as_admin)
    assert response.status_code == status_code


def test_update_role(client, user_role_id, auth_as_admin):
    response = client.put(f"auth/v1/roles/{user_role_id}", json={"name": "new name"}, headers=auth_as_admin)
    assert response.status_code == HTTPStatus.NO_CONTENT

    response = client.get(f"auth/v1/roles/{user_role_id}", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("name") == "new name"


@pytest.mark.parametrize(
    "role_id_fixture, query, status_code",
    [
        ("user_role_id", {"invalid key": "new_name"}, HTTPStatus.BAD_REQUEST),
        ("user_role_id", {"name": "new_name", "excess_key": "value"}, HTTPStatus.NO_CONTENT),
        ("invalid_uuid", {"name": "new_name"}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ("non_exist_uuid", {"name": "new_name"}, HTTPStatus.NOT_FOUND),
    ],
)
def test_update_role_errors(role_id_fixture, query, status_code, client, auth_as_admin, request):
    role_id = request.getfixturevalue(role_id_fixture)
    response = client.put(f"auth/v1/roles/{role_id}", json=query, headers=auth_as_admin)
    assert response.status_code == status_code


def test_delete_role(client, user_role_id, auth_as_admin):
    response = client.delete(f"auth/v1/roles/{user_role_id}", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.NO_CONTENT

    response = client.get(f"auth/v1/roles/{user_role_id}", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    "role_id, status_code",
    [
        ("not_uuid", HTTPStatus.UNPROCESSABLE_ENTITY),
        ("7f32cd4a-7981-436d-bba7-78169acbbb5d", HTTPStatus.NOT_FOUND),
    ],
)
def test_delete_role_errors(role_id, status_code, client, auth_as_admin):
    response = client.delete(f"auth/v1/roles/{role_id}", headers=auth_as_admin)
    assert response.status_code == status_code


def test_no_default_role(client, example_user_id, auth_as_admin):
    response = client.get(f"auth/v1/users/{example_user_id}/roles", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert response.json == []


def test_get_all_roles_of_user(client, example_with_roles_user_id, auth_as_admin):
    response = client.get(f"auth/v1/users/{example_with_roles_user_id}/roles", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 3
    assert set(role["name"] for role in response.json) == {"user", "subscriber", "admin"}


@pytest.mark.parametrize(
    "user_id, status_code",
    [
        ("not_uuid", HTTPStatus.UNPROCESSABLE_ENTITY),
        ("7f32cd4a-7981-436d-bba7-78169acbbb5d", HTTPStatus.NOT_FOUND),
    ],
)
def test_get_all_roles_of_user_errors(user_id, status_code, client, auth_as_admin):
    response = client.get(f"auth/v1/users/{user_id}/roles", headers=auth_as_admin)
    assert response.status_code == status_code


def test_add_role_to_user(client, example_user_id, user_role_id, auth_as_admin):
    response = client.post(f"auth/v1/users/{example_user_id}/roles/{user_role_id}", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.CREATED
    assert len(response.json) == 1
    assert response.json[0]["name"] == "user"

    response = client.get(f"auth/v1/users/{example_user_id}/roles", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert response.json[0]["name"] == "user"


@pytest.mark.parametrize(
    "user_id_fixture, role_id_fixture, status_code",
    [
        ("example_user_id", "invalid_uuid", HTTPStatus.UNPROCESSABLE_ENTITY),
        ("example_user_id", "non_exist_uuid", HTTPStatus.NOT_FOUND),
        ("invalid_uuid", "user_role_id", HTTPStatus.UNPROCESSABLE_ENTITY),
        ("non_exist_uuid", "user_role_id", HTTPStatus.NOT_FOUND),
    ],
)
def test_add_role_to_user_errors(user_id_fixture, role_id_fixture, status_code, client, auth_as_admin, request):
    user_id = request.getfixturevalue(user_id_fixture)
    role_id = request.getfixturevalue(role_id_fixture)
    response = client.post(f"auth/v1/users/{user_id}/roles/{role_id}", headers=auth_as_admin)
    assert response.status_code == status_code


def test_delete_role_from_user(client, example_with_roles_user_id, auth_as_admin, user_role_id):
    response = client.delete(f"auth/v1/users/{example_with_roles_user_id}/roles/{user_role_id}", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 2
    assert set(role["name"] for role in response.json) == {"subscriber", "admin"}


@pytest.mark.parametrize(
    "user_id_fixture, role_id_fixture, status_code",
    [
        ("example_with_roles_user_id", "invalid_uuid", HTTPStatus.UNPROCESSABLE_ENTITY),
        ("example_with_roles_user_id", "non_exist_uuid", HTTPStatus.NOT_FOUND),
        ("invalid_uuid", "user_role_id", HTTPStatus.UNPROCESSABLE_ENTITY),
        ("non_exist_uuid", "user_role_id", HTTPStatus.NOT_FOUND),
    ],
)
def test_delete_role_from_user_errors(user_id_fixture, role_id_fixture, status_code, client, auth_as_admin, request):
    user_id = request.getfixturevalue(user_id_fixture)
    role_id = request.getfixturevalue(role_id_fixture)
    response = client.delete(f"auth/v1/users/{user_id}/roles/{role_id}", headers=auth_as_admin)
    assert response.status_code == status_code
