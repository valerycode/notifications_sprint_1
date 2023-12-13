import datetime
from uuid import UUID

import orjson
from pydantic import BaseModel, Field, validator


def orjson_dumps(v, *, default):
    # orjson.dumps возвращает bytes, а pydantic требует unicode, поэтому декодируем
    return orjson.dumps(v, default=default).decode()


class CoreModel(BaseModel):
    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        # позволит использовать в названии полей псевдонимы
        allow_population_by_field_name = True


class Notice(CoreModel):
    x_request_id: str | None  # для трассировки сообщений
    notice_id: UUID  # id сообщения
    users_id: list[UUID]  # список на рассылку, может быть 1
    template_id: UUID  # шаблон сообщения
    extra: dict = Field(default_factory=dict)  # дополнительные поля для сообщения
    transport: str  # транспорт - 'mail', 'sms', 'ws', 'push',....
    msg_type: str  # 'info', 'promo', ....
    priority: int = 0  #
    expire_at: datetime.datetime  #

    @validator("x_request_id")
    def validate_request_id(cls, value):
        # заменяем None на текст, иначе jaeger ругается
        if value is None:
            return "request_id: None"
        return value

    @validator("expire_at")
    def validate_expire_at(cls, date):
        # если дата без часового пояса - это UTC
        if not date.tzinfo:
            return date.replace(tzinfo=datetime.timezone.utc)
        return date


class Message(CoreModel):
    x_request_id: str | None  # для трассировки сообщений
    notice_id: UUID  #
    msg_id: UUID  #
    user_id: UUID  #
    user_tz: str  #
    msg_meta: dict  #
    msg_body: str  #
    expire_at: datetime.datetime  #


class UserInfo(CoreModel):
    user_id: UUID
    email: str | None
    phone: str | None
    username: str
    time_zone: str = "UTC"
    reject_notice: list[str] = Field(default_factory=list)
