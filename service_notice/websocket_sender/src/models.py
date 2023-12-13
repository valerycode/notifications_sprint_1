from uuid import UUID

from pydantic import BaseModel, Field


class WebsocketNotification(BaseModel):
    x_request_id: str
    notice_id: UUID
    msg_id: UUID
    user_id: UUID
    msg_meta: dict = Field(default_factory=dict)
    msg_body: str
