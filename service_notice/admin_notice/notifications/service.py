import logging
import requests
import uuid
from datetime import datetime, timedelta

from config.components.common import API_NOTIFICATIONS_URL
from .schemas import Message

logger = logging.getLogger(__name__)


def generate_message_for_sending(notification):
    expire_at = notification.scheduled_time + timedelta(days=1)
    users = []
    if notification.users_ids is not None:
        for id in notification.users_ids:
            try:
                users.append(uuid.UUID(id))
            except Exception as error:
                logger.error(f'During converting user_id {id} to UUID error occurred - {error}')
                continue
    message = Message(x_request_id=str(uuid.uuid4()),
                      notice_id=notification.id,
                      users_id=users,
                      template_id=notification.template_id,
                      extra={},
                      transport=notification.transport,
                      priority=0,
                      msg_type=notification.type,
                      expire_at=expire_at)
    return message


def send_message(message: Message):
    response = requests.post(f'{API_NOTIFICATIONS_URL}/api/v1/publish', data=message.json(),
                             headers={'X-Request-Id': message.x_request_id})
    return response
