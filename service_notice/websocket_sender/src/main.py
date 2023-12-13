import asyncio
import logging

import backoff
import websockets
from aio_pika import connect
from aio_pika.abc import AbstractIncomingMessage
from aiormq import AMQPConnectionError
from pydantic import ValidationError
from websockets.server import WebSocketServerProtocol

import logging_config  # noqa
from config import settings
from models import WebsocketNotification
from utils import get_user_id

ws_connections: dict[str, WebSocketServerProtocol] = {}

logger = logging.getLogger()


async def handler(ws: WebSocketServerProtocol):
    global ws_connections
    token = await ws.recv()
    if (user_id := get_user_id(token)) is None:
        await ws.close(1011, "Invalid JWT token")
        return

    ws_connections[user_id] = ws
    logger.info("Connected user %s", user_id)
    try:
        await ws.wait_closed()
    finally:
        del ws_connections[user_id]
        logger.info("Disconnected user %s", user_id)


async def send_by_websocket(message: AbstractIncomingMessage) -> None:
    global ws_connections
    try:
        notification = WebsocketNotification.parse_raw(message.body)
    except ValidationError:
        logger.exception("Error on parsing message body %s", message.body)
        return

    if (ws := ws_connections.get(str(notification.user_id))) is not None:
        await ws.send(notification.msg_body)


@backoff.on_exception(backoff.expo, AMQPConnectionError, max_time=60, raise_on_giveup=True)
async def init_rabbit():
    connection = await connect(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        login=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD,
    )
    return connection


async def process_notifications():
    connection = await init_rabbit()
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(settings.WEBSOCKET_QUEUE)
        logger.info("Start listening queue %s", settings.WEBSOCKET_QUEUE)
        await queue.consume(send_by_websocket, no_ack=True)
        await asyncio.Future()  # runs forever


async def main():
    async with websockets.serve(handler, settings.WEBSOCKET_HOST, settings.WEBSOCKET_PORT):
        logger.info("Started websocket server on %s:%s", settings.WEBSOCKET_HOST, settings.WEBSOCKET_PORT)
        await process_notifications()


if __name__ == "__main__":
    asyncio.run(main())
