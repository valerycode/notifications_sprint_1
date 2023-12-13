from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseSettings, Field

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR.parent / ".env.local"
VAR_DIR = BASE_DIR / "var/"
LOG_DIR = VAR_DIR / "log/"
LOG_FILE = LOG_DIR / "auth.log"

SWAGGER_CONFIG = {"swagger_ui": True, "specs_route": "/auth/openapi/", "openapi": "3.0.3", "uiversion": 3}


class Config(BaseSettings):
    SECRET_KEY: str = Field(..., env="AUTH_SECRET_KEY")
    DEBUG: bool = Field(False, env="AUTH_DEBUG")
    REDIS_URI: str = Field(..., env="REDIS_AUTH_DSN")
    SQLALCHEMY_DATABASE_URI: str = Field(..., env="PG_AUTH_DSN")
    JWT_SECRET_KEY: str = Field(..., env="AUTH_JWT_KEY")
    JWT_COOKIE_SECURE: bool = Field(..., env="AUTH_JWT_COOKIE_SECURE")
    OAUTH_CREDENTIALS: dict = Field(..., env="AUTH_OAUTH_CREDENTIALS")
    JWT_COOKIE_CSRF_PROTECT: bool = False
    JWT_CSRF_IN_COOKIES: bool = True
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=30)
    OPENAPI_YAML: str = str(BASE_DIR / "openapi.yaml")
    SWAGGER: dict = SWAGGER_CONFIG
    RATE_LIMIT: str = Field(..., env="AUTH_RATE_LIMIT")
    RATELIMIT_STORAGE_URI: str = Field(..., env="REDIS_AUTH_DSN")
    JAEGER_HOST_NAME: str = Field(..., env="JAEGER_HOST_NAME")
    JAEGER_PORT: int = Field(..., env="JAEGER_PORT")
    ENABLE_TRACER: bool = Field(False, env="ENABLE_TRACER")
    SERVICE_NAME: str = Field(..., env="AUTH_PROJECT_NAME")


# фласк по умолчанию ищет настройки в .env файле, в том числе в родительских папках
# поэтому для локального запуска вручную загружаем нужный файл .env.local
# в контейнере env файла не будет и настройки будут взяты из переменных окружения
load_dotenv(ENV_FILE, override=True)
flask_config = Config()
