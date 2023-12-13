import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv
from flask import testing
from werkzeug.datastructures import Headers

BASE_DIR = Path(__file__).parent.parent
ENV_TEST = BASE_DIR / ".env.test.local"

src_path = BASE_DIR / "src/"
if src_path not in sys.path:
    sys.path.insert(1, str(src_path))

import utils
from app import create_app
from app.flask_db import db
from app.services import auth_service, role_service
from config import Config


class TestClient(testing.FlaskClient):
    def open(self, *args, **kwargs):
        headers = kwargs.pop("headers", Headers())
        headers["X-Request-Id"] = "test-id"
        kwargs["headers"] = headers
        return super().open(*args, **kwargs)


@pytest.fixture(scope="session")
def app():
    # pytest видимо сам прогружает .env где найдет, а находит в корне...
    # приходится жестко перегружать
    # a в pydantic BaseSettings приоритет переменных окружения перед env файлом
    # в контейнере файла ENV_TEST не будет, ,будут использованы переменные окружения
    load_dotenv(ENV_TEST, override=True)
    flask_config = Config()
    flask_config.RATE_LIMIT = "10/minute;5/second"

    app = create_app(flask_config)

    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    with app.app_context():
        db.drop_all()
        auth_service.storage.redis.flushall()

        db.create_all()
        db.session.commit()

        utils.create_roles_and_users()

        app.test_client_class = TestClient
        yield app.test_client()

        db.session.remove()
        db.drop_all()
        auth_service.storage.redis.flushall()


@pytest.fixture(scope="module")
def module_client(app):
    with app.app_context():
        db.drop_all()
        auth_service.storage.redis.flushall()

        db.create_all()
        db.session.commit()

        utils.create_roles_and_users()

        yield app.test_client()

        db.session.remove()
        db.drop_all()
        auth_service.storage.redis.flushall()


@pytest.fixture
def example_user_id(client):
    # зависит фикстуры client, должен быть активен app_context и создан пользователь
    user = role_service.users.user_by_login("example")
    return str(user.id)


@pytest.fixture
def example_with_roles_user_id(client):
    # зависит фикстуры client, должен быть активен app_context и создан пользователь
    user = role_service.users.user_by_login("example_with_roles")
    return str(user.id)


@pytest.fixture
def example_user_tokens(client):
    """Access, refresh и csrf токены, получаемые при логине пользователя example."""
    # токены через запрос, чтобы появилась запись в storage о refresh токене
    return utils.get_tokens_by_login_reqest(client, "example", "example", "device_auth")


@pytest.fixture
def auth_as_admin(client):
    access_token = utils.create_access_token_for_user("example_admin")
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers


@pytest.fixture
def auth_as_user(client):
    access_token = utils.create_access_token_for_user("example")
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers


@pytest.fixture
def invalid_uuid():
    return "not_uuid"


@pytest.fixture
def non_exist_uuid():
    return "7f32cd4a-7981-436d-bba7-78169acbbb5d"
