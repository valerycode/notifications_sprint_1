import datetime
import logging
from abc import abstractmethod
from email.message import EmailMessage
from http import HTTPStatus

import sendgrid
from python_http_client.exceptions import HTTPError
from sendgrid.helpers.mail import From, HtmlContent, Mail, SendAt, Subject, To

from config import settings
from models import EmailNotification
from utils import get_send_datetime

logger = logging.getLogger(__name__)


class BaseSender:
    @abstractmethod
    def send(self, notice: EmailNotification, priority: int) -> EmailNotification | None:
        """Отпрравляет уведомление по email.

        В случае ошибок возвращает само уведомление для повторной отправки.
        Возвращает None при успешной отправке или превышении максимального
        количества попыток.
        """
        ...

    @staticmethod
    def check_to_resend(notice: EmailNotification) -> EmailNotification | None:
        if notice.retries == settings.MAX_RETRIES:
            return None
        notice.retries += 1
        return notice


class SendgridSender(BaseSender):
    def __init__(self):
        self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

    def send(self, notice: EmailNotification, priority: int) -> EmailNotification | None:
        message = Mail(
            from_email=From(settings.SEND_FROM_EMAIL),
            to_emails=To(notice.msg_meta.email),
            subject=Subject(notice.msg_meta.subject),
            html_content=HtmlContent(notice.msg_body),
        )
        if priority <= 1:  # сообщения с низким приоритетом можно задержать для отправки в дневное время
            send_datetime = get_send_datetime(notice.user_tz)
            message.send_at = SendAt(send_at=int(send_datetime.timestamp()))

        try:
            response = self.sendgrid_client.send(message=message)
        except HTTPError:
            logger.exception("Error on sending email notification %s", notice.json())
            return self.check_to_resend(notice)

        if response.status_code != HTTPStatus.ACCEPTED:
            logger.error("Error on sending email notification %s", notice.json())
            return self.check_to_resend(notice)

        logger.info("Send notification %s", notice.json())


class DebugSender(BaseSender):
    def send(self, notice: EmailNotification, priority: int) -> EmailNotification | None:
        message = EmailMessage()
        message["From"] = settings.SEND_FROM_EMAIL
        message["To"] = notice.msg_meta.email
        message["Subject"] = notice.msg_meta.subject
        message.set_content(notice.msg_body)
        if priority <= 1:
            send_datetime = get_send_datetime(notice.user_tz)
            send_at = send_datetime.isoformat()
        else:
            send_at = datetime.datetime.utcnow().isoformat()
        print(f"Email would be send at {send_at}")
        print(f"#---MESSAGE START---#\n{message}\n#---MESSAGE END---#\n")
        return None
