from flask import Flask
from flask_jwt_extended import JWTManager

from app.db.database import AbstractUsers


def init_jwt(app: Flask, token_srv, users: AbstractUsers):
    jwt = JWTManager()
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
        # blacklist for access
        if jwt_payload["type"] == "access":
            # access токены не проверяем на отзыв, хотя можно
            # возвращаем что не отозван
            return False

        # whitelist for refresh
        if jwt_payload["type"] == "refresh":
            jti = jwt_payload["jti"]
            user_id = jwt_payload["sub"]
            device_id = jwt_payload["device_id"]

            # если токен проходит, значит не отозван
            return not token_srv.check_token(user_id, device_id, jti)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        user_id = jwt_data["sub"]
        return users.user_by_id(user_id)
