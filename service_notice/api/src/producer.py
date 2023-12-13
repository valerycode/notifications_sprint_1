import logging
import json
from abc import abstractmethod, ABC
from fastapi.encoders import jsonable_encoder
import backoff as backoff
from aio_pika import connect, Message
from aiormq import AMQPConnectionError

from src.settings import settings


class BaseProducer(ABC):
    @abstractmethod
    async def connect_broker(self, *args):
        pass

    @abstractmethod
    async def publish(self, *args):
        pass


class RabbitMQ(BaseProducer):
    def __init__(self, dsn):
        self.dsn = dsn
        self.connection = None
        self.queue = None

    @backoff.on_exception(backoff.expo, AMQPConnectionError, max_time=60, raise_on_giveup=True)
    async def connect_broker(self):
        self.connection = await connect(self.dsn)
        logging.info("connected to rabbitmq")
        return True

    async def close(self):
        try:
            await self.connection.close()
        except Exception as e:
            logging.error("error closing connection")
            raise e

    async def create_queue(self, ):
        async with self.connection.channel() as channel:
            self.queue = await channel.declare_queue(settings.QUEUE_NAME, durable=True, arguments={"x-max-priority": 10})
            logging.info("queue created")

    async def publish(self, message: dict) -> str:
        encoded_message = jsonable_encoder(message)
        if not self.queue:
            await self.create_queue()
        async with self.connection.channel() as channel:
            await channel.default_exchange.publish(
                Message(body=json.dumps(encoded_message).encode('utf-8')),
                routing_key=self.queue.name)
        return "Message sent"
