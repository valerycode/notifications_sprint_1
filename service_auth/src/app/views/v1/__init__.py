from flask import Blueprint

from .auth_routes import auth_bp
from .me_routes import me_bp
from .oauth_routes import oauth_bp
from .role_routes import role_bp
from .user_routes import user_bp
from .userinfo_routes import userinfo_bp

auth_v1 = Blueprint("auth_v1", __name__, url_prefix="/v1")

auth_v1.register_blueprint(me_bp)
auth_v1.register_blueprint(auth_bp)
auth_v1.register_blueprint(role_bp)
auth_v1.register_blueprint(user_bp)
auth_v1.register_blueprint(oauth_bp)
auth_v1.register_blueprint(userinfo_bp)
