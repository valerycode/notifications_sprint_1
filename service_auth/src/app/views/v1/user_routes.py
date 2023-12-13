from http import HTTPStatus

from flask import Blueprint
from flask_restful import Api, Resource, reqparse

from app.core.utils import error, jwt_accept_roles, validate_uuids
from app.services import auth_service, user_service

parser = reqparse.RequestParser()
parser.add_argument("name")
parser.add_argument("email")
parser.add_argument("password")


class Users(Resource):
    def get(self, user_id):
        validate_uuids(user_id)
        user = user_service.get_user_by_id(user_id)
        return user

    def post(self):
        """Добавить пользователя"""

        name = parser.parse_args()["name"]
        email = parser.parse_args()["email"]
        password = parser.parse_args()["password"]

        if email is None:
            error("No email provided", HTTPStatus.BAD_REQUEST)
        if password is None:
            error("No password provided", HTTPStatus.BAD_REQUEST)

        if name is None:
            name = email

        user = user_service.add_user(email, password, name)
        return user, HTTPStatus.CREATED

    def patch(self, user_id):
        """
        Поменять данные пользователя
        Можно указывать не все поля, меняются только присутствующие
        """
        validate_uuids(user_id)
        name = parser.parse_args()["name"]
        password = parser.parse_args()["password"]

        user = user_service.change_user(user_id, password, name)

        return user


class UserHistory(Resource):
    def get(self, user_id):
        validate_uuids(user_id)
        return auth_service.get_user_history(user_id)


class UserSessions(Resource):
    def get(self, user_id):
        validate_uuids(user_id)
        result = user_service.get_user_sessions(user_id)
        return result


user_bp = Blueprint("user", __name__)
api = Api(user_bp, decorators=[jwt_accept_roles("admin")])
api.add_resource(Users, "/users", "/users/<user_id>")
api.add_resource(UserHistory, "/users/<user_id>/history")
api.add_resource(UserSessions, "/users/<user_id>/sessions")
