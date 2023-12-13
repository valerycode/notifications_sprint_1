from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    JWT_SECRET_KEY: str = Field("secret_jwt_key", env="WEBSOCKET_SENDER_JWT_KEY")
    DEBUG: bool = Field(True, env="WEBSOCKET_SENDER_DEBUG")
    WEBSOCKET_HOST: str = Field("localhost", env="WEBSOCKET_SENDER_HOST")
    WEBSOCKET_PORT: str = Field(8888, env="WEBSOCKET_SENDER_PORT")
    RABBITMQ_USER: str = Field("user", env="RABBITMQ_NOTICE_USER")
    RABBITMQ_PASSWORD: str = Field("password", env="RABBITMQ_NOTICE_PASSWORD")
    RABBITMQ_HOST: str = Field("localhost", env="RABBITMQ_NOTICE_HOST")
    RABBITMQ_PORT: int = Field(5672, env="RABBITMQ_NOTICE_PORT")
    WEBSOCKET_QUEUE: str = "websocket"


settings = Settings()
