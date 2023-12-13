from pathlib import Path

from pydantic import BaseSettings, Field

BASE_DIR = Path(__file__).parent.parent
ENV_FILE = BASE_DIR.parent / ".env.local"


class Settings(BaseSettings):
    PROJECT_NAME: str = "notice service:etl"

    PG_URI: str = Field(..., env="NOTICE_ETL_PG_URI")
    AUTH_SERVICE_URI: str = Field(..., env="NOTICE_ETL_AUTH_SERVICE_URI")
    AUTH_API_PATH: str = "/auth/v1/userinfo"
    REDIS_URI: str = Field(..., env="NOTICE_ETL_REDIS_URI")
    RABBITMQ_URI: str = Field(..., env="NOTICE_ETL_RABBITMQ_URI")
    DEBUG: bool = Field(True, env="NOTICE_ETL_DEBUG")
    SECRET_KEY: str = Field("secret_key", env="NOTICE_ETL_SECRET_KEY")

    JAEGER_HOST_NAME: str = Field("localhost", env="JAEGER_HOST_NAME")
    JAEGER_PORT: int = Field(6831, env="JAEGER_PORT")
    ENABLE_TRACER: bool = Field(False, env="ENABLE_TRACER")

    ENABLE_SENTRY: bool = Field(False, env="ENABLE_SENTRY")
    SENTRY_DSN: str = Field("<sentry dsn>", env="SENTRY_DSN")
    RELEASE_VERSION: str = Field("notice-service@1.0.0", env="RELEASE_VERSION")


settings = Settings(_env_file=ENV_FILE)
