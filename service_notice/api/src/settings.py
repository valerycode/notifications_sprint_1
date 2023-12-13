from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    PROJECT_NAME: str = Field("Producer", env="UGC_PROJECT_NAME")
    PRODUCER_DSN: str = Field(env="RABBITMQ_NOTICE_URI")
    QUEUE_NAME: str = Field("notice", env="QUEUE_NAME")
    ENABLE_TRACER: bool = Field(False, env="ENABLE_TRACER")
    JAEGER_HOST_NAME: str = Field("localhost", env="JAEGER_HOST_NAME")
    JAEGER_PORT: int = Field(6831, env="JAEGER_PORT")
    DEBUG: bool = Field(True, env="UGC_DEBUG")


settings = Settings(_env_file="../.env")
