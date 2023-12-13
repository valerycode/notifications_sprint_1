import logging

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.producer import RabbitMQ
from src.settings import settings
from src.tracer import init_tracer

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)

producer = RabbitMQ(settings.PRODUCER_DSN)


@app.on_event("startup")
async def startup_event():
    logging.debug("app startup")
    if not await producer.connect_broker():
        raise SystemExit("can't connect to rabbitmq brokers")
    init_tracer(app)


@app.on_event("shutdown")
async def shutdown_event():
    logging.debug("app shutdown")
    await producer.close()
