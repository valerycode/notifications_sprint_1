from http import HTTPStatus

from flask import Blueprint, current_app

from app.core.utils import error
from app.services.oauth_service import OAuthSignIn, login_by_social

oauth_bp = Blueprint("oauth", __name__)


@oauth_bp.route("/callback/<provider>")
def oauth_callback(provider):
    oauth = OAuthSignIn.get_provider(provider)
    if not oauth:
        error("Auth provider not found", HTTPStatus.NOT_FOUND)

    social_id, username, email = oauth.callback()
    if social_id is None:
        error("Authentication failed", HTTPStatus.UNAUTHORIZED)
    current_app.logger.debug(
        f'login user from social email:"{email}" '
        f'username:"{username}" social_net:"{provider}" social_user_id:"{social_id}"'
    )
    response = login_by_social(provider, social_id, username, email)

    return response


@oauth_bp.route("/authorize/<provider>")
def oauth_authorize(provider):
    oauth = OAuthSignIn.get_provider(provider)
    if not oauth:
        error("Auth provider not found", HTTPStatus.NOT_FOUND)
    return oauth.authorize()
