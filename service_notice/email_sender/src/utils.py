import logging
from datetime import datetime, time, timedelta

import pytz

from config import settings

logger = logging.getLogger(__name__)


def get_send_datetime(
    user_tz: str, time_start: time = settings.SEND_AFTER_TIME, time_end: time = settings.SEND_BEFORE_TIME
) -> datetime:
    try:
        user_now_datetime = datetime.now(tz=pytz.timezone(user_tz))
    except pytz.exceptions.UnknownTimeZoneError:
        logger.exception("Invalid timezone name %s", user_tz)
        return datetime.utcnow()

    user_now_time = user_now_datetime.time()
    if user_now_time < time_start:
        dt = timedelta(hours=(time_start.hour - user_now_time.hour))
    elif time_start <= user_now_time <= time_end:
        dt = timedelta()
    else:
        dt = timedelta(hours=(24 - user_now_time.hour + time_start.hour))

    return user_now_datetime + dt
