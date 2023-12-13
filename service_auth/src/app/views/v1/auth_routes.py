from http import HTTPStatus

from flask import Blueprint, jsonify, redirect, request
from flask_jwt_extended import get_jwt, jwt_required, set_access_cookies, set_refresh_cookies, unset_jwt_cookies

from app.core.utils import error
from app.flask_limits import limit_by_ip, limit_by_user_id
from app.services import auth_service, token_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
@limit_by_ip
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    device_name = request.headers.get("User-Agent")
    remote_ip = request.remote_addr

    if email is None or password is None:
        return error("No email or password", HTTPStatus.BAD_REQUEST)

    user = auth_service.auth(email, password)

    access_token, refresh_token = token_service.new_tokens(user, device_name)
    # ttl - time of session life
    ttl = token_service.get_refresh_token_expires()
    auth_service.new_session(user.id, device_name, remote_ip, ttl)

    response = jsonify(access_token=access_token, refresh_token=refresh_token)
    set_refresh_cookies(response, refresh_token)
    set_access_cookies(response, access_token)

    return response


@auth_bp.route("/logout", methods=["GET", "POST"])
@jwt_required()
@limit_by_user_id
def logout():
    token = get_jwt()
    user_id = token["sub"]
    device_id = token["device_id"]
    remote_ip = request.remote_addr
    device_name = request.headers.get("User-Agent")

    token_service.remove_token(user_id, device_id)
    auth_service.close_session(user_id, device_name, remote_ip)
    if request.method == "POST":
        response = jsonify({"msg": "logout"})
    else:
        response = redirect("/")

    unset_jwt_cookies(response)

    return response


@auth_bp.route("/refresh", methods=["GET", "POST"])
@jwt_required(refresh=True)
@limit_by_user_id
def refresh():
    payload = get_jwt()

    device_name = request.headers.get("User-Agent")
    if not token_service.is_valid_device(device_name, payload):
        return error("Token invalidated", HTTPStatus.UNAUTHORIZED)

    user_id = payload["sub"]
    device_id = payload["device_id"]
    old_token_id = payload["jti"]
    remote_ip = request.remote_addr
    access_token, refresh_token = token_service.refresh_tokens(user_id, device_id, old_token_id)

    # ttl - time of session life
    ttl = token_service.get_refresh_token_expires()
    auth_service.refresh_session(user_id, device_name, remote_ip, ttl)

    response = jsonify(access_token=access_token, refresh_token=refresh_token)
    set_refresh_cookies(response, refresh_token)
    set_access_cookies(response, access_token)

    return response
