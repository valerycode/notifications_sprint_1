from http import HTTPStatus

from flask import Blueprint, jsonify, request

from app.core.utils import error, validate_uuids, secret_key_required
from app.services import user_service
from config import flask_config

userinfo_bp = Blueprint("userinfo", __name__)

secret_key = flask_config.SECRET_KEY
@userinfo_bp.post("/userinfo")
#@jwt_accept_roles("admin")
#@jwt_required()
@secret_key_required(secret_key)
def get_users_info():
    user_ids = request.json.get("user_ids", None)

    if user_ids is None:
        return error("No ids provided", HTTPStatus.BAD_REQUEST)

    if not isinstance(user_ids, list):
        return error("Ids must be provided as list", HTTPStatus.BAD_REQUEST)

    validate_uuids(*user_ids)

    users_info = user_service.get_users_info(user_ids)
    response = jsonify(users_info=users_info)
    return response
