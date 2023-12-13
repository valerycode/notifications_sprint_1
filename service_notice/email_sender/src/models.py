from uuid import UUID

from pydantic import BaseModel


class EmailMetadata(BaseModel):
    email: str
    subject: str


class EmailNotification(BaseModel):
    x_request_id: str
    notice_id: UUID
    msg_id: UUID
    user_id: UUID
    user_tz: str
    msg_meta: EmailMetadata
    msg_body: str
    retries: int = 0
