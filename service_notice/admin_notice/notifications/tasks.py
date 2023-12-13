import logging
from http import HTTPStatus

from config.celery_app import app
from django.utils import timezone

from .models import Notification
from .service import generate_message_for_sending, send_message

logger = logging.getLogger(__name__)


@app.task
def send_notifications():
    notifications = Notification.objects.filter(status='waiting', scheduled_time__lte=timezone.now())
    for notification in notifications:
        try:
            message = generate_message_for_sending(notification)
        except Exception as error:
            logger.debug(f'Generating message for notification with'
                         f' UUID {notification.id} failed, error occurred - {error}')
            continue
        else:
            try:
                response = send_message(message)
            except Exception as error:
                logger.debug(f'During sending message to API the error occurred - {error}')
            else:
                if response.status_code == HTTPStatus.OK:
                    notification.status = 'done'
                    logger.debug(f'Notification with UUID {notification.id} was successfully sent to API')
                else:
                    notification.status = 'failed'
                    logger.debug(f'Notification with UUID {notification.id} was'
                                 f' not sent to API. Response from API - {response.status_code}.'
                                 f' Response - {response.text}')
                notification.save()
