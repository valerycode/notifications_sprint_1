"""
 test route with tiny frontend
"""
from flask import Blueprint, render_template
from flask_jwt_extended import get_jwt, jwt_required

default_bp = Blueprint("default", __name__)


@default_bp.get("/")
@jwt_required(optional=True)
def get_index():
    token = get_jwt()
    user_id = ""
    user_name = "Anon user"
    # если токен есть - значит пользователь залогинен, возвращаем его же
    if token:
        user_id = token["sub"]
        user_name = token["name"]

    return render_template("index.html", user_name=user_name, user_id=user_id)


@default_bp.get("/login")
@jwt_required(optional=True)
def get_auth():
    token = get_jwt()
    # если токен есть - значит пользователь залогинен, возвращаем его же
    if token:
        user_id = token["sub"]
        user_name = token["name"]
        return render_template("index.html", user_name=user_name, user_id=user_id)

    return render_template("auth.html")
