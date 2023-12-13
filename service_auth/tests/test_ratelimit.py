from http import HTTPStatus


def repeat_request(repeats, method_call, *args, **kwargs):
    for i in range(repeats):
        response = method_call(*args, **kwargs)
    return response


def test_rate_limit_by_user_id(client, example_user_id, auth_as_user):
    response = repeat_request(5, client.get, "/auth/v1/users/me/", headers=auth_as_user)
    assert response.status_code == HTTPStatus.OK


def test_rate_limit_by_user_id_exceed(client, example_user_id, auth_as_user):
    response = repeat_request(6, client.get, "/auth/v1/users/me/", headers=auth_as_user)
    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS


def test_rate_limit_by_ip_address(client):
    response = repeat_request(5, client.post, "/auth/v1/login", json={"email": "example", "password": "example"})
    assert response.status_code == HTTPStatus.OK


def test_rate_limit_by_ip_address_exceed(client, example_user_id, auth_as_user):
    # def test_rate_limit_by_ip_address_exceed(client):
    response = repeat_request(11, client.post, "/auth/v1/login", json={"email": "example", "password": "example"})
    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS


def test_no_limit_for_admin_required_routes(client, auth_as_admin):
    response = repeat_request(6, client.get, "/auth/v1/roles", headers=auth_as_admin)
    assert response.status_code == HTTPStatus.OK
