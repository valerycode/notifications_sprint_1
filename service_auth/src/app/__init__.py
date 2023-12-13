from flasgger import Swagger
from flask import Flask
from flask_limiter import RateLimitExceeded
from flask_migrate import Migrate

from app.core.exceptions import AuthServiceError, http_error_handler, ratelimit_error_handler
from app.core.utils import require_header_request_id
from app.db.database import Actions, Roles, SocialAccounts, Users
from app.db.storage import Storage
from app.flask_cli import init_cli
from app.flask_db import init_db
from app.flask_jwt import init_jwt
from app.flask_limits import init_limiter
from app.flask_tracing import init_tracer
from app.services import auth_service as auth_srv
from app.services import oauth_service as oauth_srv
from app.services import role_service as role_srv
from app.services import token_service as token_srv
from app.services import user_service as user_srv
from app.views import auth_bp
from app.views.default_routes import default_bp


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    app.config["JWT_TOKEN_LOCATION"] = ["headers", "json", "cookies"]  # - так не требует csrf?
    app.config["JWT_REFRESH_COOKIE_PATH"] = "/auth/v1/refresh"

    db = init_db(app)
    # это для  UUID->JSON
    app.config["RESTFUL_JSON"] = {"default": str}
    # обертка редис
    storage = Storage(config.REDIS_URI)
    # обертка DB
    users = Users()
    roles = Roles()
    actions = Actions()
    socials = SocialAccounts()

    Swagger(app, template_file=config.OPENAPI_YAML)
    Migrate(app, db)
    init_cli(app)

    init_limiter(app)

    # внедряем зависимости в модули
    auth_srv.users = users
    auth_srv.actions = actions
    auth_srv.storage = storage

    token_srv.users = users
    token_srv.storage = storage

    role_srv.users = users
    role_srv.roles = roles

    user_srv.users = users
    user_srv.socials = socials

    oauth_srv.users = users
    oauth_srv.social_accounts = socials

    init_jwt(app, token_srv, users)

    app.register_blueprint(auth_bp)
    app.register_blueprint(default_bp)

    app.register_error_handler(AuthServiceError, http_error_handler)
    app.register_error_handler(RateLimitExceeded, ratelimit_error_handler)

    if config.ENABLE_TRACER:
        app.before_request(require_header_request_id)
        init_tracer(app)

    return app
