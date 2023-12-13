from http import HTTPStatus
from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from app.core.utils import error
from app.flask_limits import limit_by_ip, limit_by_user_id
from app.services import auth_service
from app.services.oauth_service import del_user_social, get_user_socials
from app.services.role_service import get_user_roles
from app.services.user_service import add_user, change_user, get_user_by_id, get_user_sessions, logout_all

me_bp = Blueprint("me", __name__, url_prefix="/users/me")


@me_bp.get("/")
@jwt_required()
@limit_by_user_id
def get_info():
    """get user data"""
    token = get_jwt()
    user_id = token["sub"]
    user = get_user_by_id(user_id)
    return jsonify(user)


@me_bp.post("/")
@jwt_required(optional=True)
@limit_by_ip
def new_user():
    """new user create or return exist user if logined"""
    token = get_jwt()
    # если токен есть - значит пользователь залогинен, возвращаем его же
    if token:
        user_id = token["sub"]
        user = get_user_by_id(user_id)
        return jsonify(user), HTTPStatus.IM_A_TEAPOT

    email = request.json.get("email", None)
    password = request.json.get("password", None)
    name = request.json.get("name", None)
    if not (email and password):
        error("email and password info required", HTTPStatus.BAD_REQUEST)

    user = add_user(email, password, name)

    return jsonify(user), HTTPStatus.CREATED


@me_bp.patch("/")
@jwt_required()
@limit_by_user_id
def change_info():
    token = get_jwt()
    user_id = token["sub"]

    password = request.json.get("password", None)
    name = request.json.get("name", None)
    user = change_user(user_id, password, name)

    return jsonify(user)


@me_bp.get("/roles")
@jwt_required()
@limit_by_user_id
def get_roles():
    token = get_jwt()
    user_id = token["sub"]

    roles = get_user_roles(user_id)
    return jsonify(roles)


@me_bp.get("/history")
@jwt_required()
@limit_by_user_id
def get_history():
    token = get_jwt()
    user_id = token["sub"]

    history = auth_service.get_user_history(user_id)
    return jsonify(history)


@me_bp.get("/sessions")
@jwt_required()
@limit_by_user_id
def get_sessions():
    token = get_jwt()
    user_id = token["sub"]

    sessions = get_user_sessions(user_id)
    return jsonify(sessions)


@me_bp.delete("/sessions")
@jwt_required()
@limit_by_user_id
def close_all_sessions():
    token = get_jwt()
    user_id = token["sub"]

    logout_all(user_id)
    return "", HTTPStatus.NO_CONTENT


@me_bp.get("/socials")
@jwt_required()
def get_socials():
    token = get_jwt()
    user_id = token["sub"]

    socials = get_user_socials(user_id)
    return jsonify(socials)


@me_bp.delete("/socials/<social_id>")
@jwt_required()
def del_socials(social_id: UUID):
    token = get_jwt()
    user_id = token["sub"]

    socials = del_user_social(user_id, social_id)
    return jsonify(socials)
