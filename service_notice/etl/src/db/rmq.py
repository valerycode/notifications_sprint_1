import logging

import backoff
import pika
from pika.exceptions import AMQPConnectionError


class RabbitMQ:
    @backoff.on_exception(backoff.expo, AMQPConnectionError, max_time=60)
    def __init__(self, uri: str):
        logging.debug("start rabbitmq")

        parameters = pika.URLParameters(uri)
        self.connection = pika.BlockingConnection(parameters=parameters)

    def close(self):
        if self.connection:
            self.connection.close()
            logging.debug("close rabbitmq")


db: RabbitMQ | None = None
