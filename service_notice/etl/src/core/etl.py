import datetime
import logging
import math
import time
import uuid
from typing import Generator

import orjson
import pika
from jinja2 import Template
from opentelemetry import trace

from core.constants import QUEUE_NOTICE, Mark, Transport
from core.models import Message, Notice, UserInfo
from core.utils import get_ttl_from_datetime
from db.auth_api import get_users_info_from_auth
from db.pg import get_template_from_db
from db.rmq import RabbitMQ
from db.storage import get_mark, set_mark

# глушим вывод модуля rabbitmq, иначе он спамит в режиме debug
logging.getLogger("pika").setLevel(logging.WARNING)

tracer = trace.get_tracer(__name__)


# TODO можно завернуть в кэш
def get_template(template_id: uuid.UUID) -> Template:
    subject, template_str = get_template_from_db(str(template_id))
    template = Template(template_str)
    template.subject = subject
    return template


def get_users_info(request_id: str, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, UserInfo]:
    result = get_users_info_from_auth(request_id, user_ids)
    return result


def mark_processed(notice_id: uuid.UUID, user_id: uuid.UUID | int, result=Mark.QUEUED, ttl=24 * 60 * 60):
    # добавляем к ttl 1мин чтобы гонок не было и если есть сообщение - в редис точно была отметка
    set_mark(notice_id, user_id, result, ttl + 60)


def is_processed(notice_id: uuid.UUID, user_id: uuid.UUID | int) -> bool:
    result = get_mark(notice_id, user_id)
    return result is not None


class Extractor:
    def __init__(self, rmq: RabbitMQ):
        self.channel = rmq.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.channel.queue_declare(queue="notice", durable=True, arguments={"x-max-priority": 10})
        self.current_delivery_tag = None

    def get_data(self):
        method_frame, header_frame, body = self.channel.basic_get(QUEUE_NOTICE, auto_ack=False)
        if method_frame:
            logging.debug("extract message:{0}".format(body))
            self.current_delivery_tag = method_frame.delivery_tag
            notice_dict = orjson.loads(body)
            return Notice(**notice_dict)

    def mark_done(self):
        self.channel.basic_ack(self.current_delivery_tag)


class Transformer:
    @staticmethod
    def get_msg_meta(data: Notice, user_info: UserInfo, subject: str = "Movies") -> dict | None:
        transport = data.transport
        match transport:
            case Transport.EMAIL:
                if user_info.email:
                    return {"email": user_info.email, "subject": subject}

            case Transport.SMS:
                if user_info.phone:
                    return {"phone": user_info.phone}

            case Transport.WEBSOCKET:
                # без понятия что нужно для сокетов. наверное только user_id, но он есть в сообщении
                return {}

        # если ничего не выдали до этого, значит вернем None и сообщение не отправится
        return None

    def transform(self, data: Notice):
        def user_info_lst(request_id: str, user_lst: list[uuid.UUID], batch_size=100):
            """
            Для оптимизации - выполнение запросов пачками к auth
            Пачка не больше batch_size
            """
            window_count = math.ceil(len(user_lst) / batch_size)
            for window in range(window_count):
                start = window * batch_size
                users_batch = user_lst[start : start + batch_size]
                user_info_dict = get_users_info(request_id, users_batch)
                # TODO что делать с пользователями без user_info?
                if len(users_batch) > len(user_info_dict):
                    logging.debug("Not found users info: {0}".format(len(users_batch) - len(user_info_dict)))
                yield from user_info_dict.values()

        with tracer.start_as_current_span("etl_transform") as span:
            span.set_attribute("http.request_id", data.x_request_id)
            span.set_attribute("transport", data.transport)

            if data.expire_at < datetime.datetime.now(tz=datetime.timezone.utc):
                logging.debug("message rejected due expire date: {0}".format(data.expire_at))
                return None

            template = get_template(data.template_id)
            notice_id = data.notice_id
            ttl = get_ttl_from_datetime(data.expire_at)
            # узнаю повторная ли это обработка
            is_repeat = is_processed(notice_id, 0)
            users = data.users_id

            if not is_repeat:
                mark_processed(notice_id, 0, ttl=ttl)
            else:
                # фильтруем пользователей, оставляя только тех, что еще не обрабатывали.
                # не очень то оптимально....
                # с учетом того, что данные отправляются последовательно, можно
                # в дальнейшем оптимизировать поиск последнего обработанного пользователя
                users = list(filter(lambda x: not is_processed(notice_id, x), users))

            for user_info in user_info_lst(data.x_request_id, users):
                # пропускаем, если пользователь отказался от некоторых рассылок
                if data.msg_type in user_info.reject_notice:
                    # помечаем сообщение как отвергнутое
                    mark_processed(data.notice_id, user_info.user_id, Mark.REJECTED_USER, ttl)
                    continue

                msg_body = template.render(user_info.dict() | data.extra)
                msg_meta = self.get_msg_meta(data, user_info, template.subject)
                # для случаев, когда не можем отправить сообщение,
                # потому что не хватает данных для отправки, например телефона
                if msg_meta is None:
                    mark_processed(data.notice_id, user_info.user_id, Mark.REJECTED_NODATA, ttl)
                    continue

                message = Message(
                    x_request_id=data.x_request_id,
                    notice_id=data.notice_id,
                    msg_id=uuid.uuid4(),
                    user_id=user_info.user_id,
                    user_tz=user_info.time_zone,
                    msg_meta=msg_meta,
                    msg_body=msg_body,
                    expire_at=data.expire_at,
                )
                yield data.transport, data.priority, message


class Loader:
    def __init__(self, rmq: RabbitMQ):
        self.channel = rmq.connection.channel()

    def send_message(self, queue: str, msg: Message, ttl: int, priority: int):
        properties = pika.BasicProperties(expiration=str(ttl * 1000), delivery_mode=2, priority=priority)
        self.channel.basic_publish(exchange="", routing_key=queue, properties=properties, body=msg.json())
        logging.debug("message loaded in [{1}]: {0}".format(msg.dict(), queue))

    def load(self, data: Generator[tuple[str, int, Message], None, None]):
        for transport, priority, msg in data:
            with tracer.start_as_current_span("etl_load") as span:
                # делаем трассировку
                span.set_attribute("http.request_id", msg.x_request_id)
                span.set_attribute("transport", transport)

                # ставим в очередь на отправку
                ttl = get_ttl_from_datetime(msg.expire_at)
                self.send_message(queue=transport, msg=msg, ttl=ttl, priority=priority)

                # помечаем как обработанное
                mark_processed(msg.notice_id, msg.user_id, Mark.QUEUED, ttl)


class ETL:
    is_run = False

    def __init__(self, rmq: RabbitMQ):
        self.extractor = Extractor(rmq)
        self.transformer = Transformer()
        self.loader = Loader(rmq)

    def stop(self):
        self.is_run = False
        logging.info("stop etl")

    def run(self):
        self.is_run = True
        while self.is_run:
            data = self.extractor.get_data()
            if not data:
                time.sleep(0.1)
                continue

            transformed_data = self.transformer.transform(data)

            self.loader.load(transformed_data)

            # если в процессе ничего не упало - считаем что задание выполнено
            self.extractor.mark_done()
