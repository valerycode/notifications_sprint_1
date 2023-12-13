from flask import Blueprint

from app.views.v1 import auth_v1

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
auth_bp.register_blueprint(auth_v1)
