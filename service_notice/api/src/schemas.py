from datetime import datetime
from types import NoneType
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

import orjson


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class BaseModelMixin(BaseModel):

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class Message(BaseModelMixin):
    x_request_id: str | NoneType
    notice_id: UUID
    users_id: List[UUID]
    template_id: UUID | NoneType = 1
    extra: dict = Field(default_factory=dict)
    transport: str
    priority: int | NoneType = 0
    msg_type: str | NoneType
    expire_at: datetime
