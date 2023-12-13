from http import HTTPStatus

from flask import jsonify
from flask_limiter import RateLimitExceeded


class AuthServiceError(Exception):
    def __init__(self, status_code, detail, *args):
        super().__init__(args)
        self.status_code = status_code
        self.detail = detail


def http_error_handler(err: AuthServiceError):
    return jsonify({"msg": err.detail}), err.status_code


def ratelimit_error_handler(err: RateLimitExceeded):
    return jsonify({"msg": f"Ratelimit exceeded {err.description}"}), HTTPStatus.TOO_MANY_REQUESTS
