import logging
from http import HTTPStatus
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from src.settings import settings


def init_tracer(app: FastAPI) -> None:
    if settings.ENABLE_TRACER:
        logging.debug("Jaeger tracer is ON")
        configure_tracer()
        FastAPIInstrumentor.instrument_app(app)
        app.router.dependencies += [Depends(require_header_request_id)]
    else:
        logging.debug("Jaeger tracer is OFF")


def configure_tracer() -> None:
    """Настройка трейсера Jaeger"""

    provider = TracerProvider(resource=Resource.create({"service.name": settings.PROJECT_NAME}))
    # Sets the global default tracer provider
    trace.set_tracer_provider(provider)

    jaeger_exporter = JaegerExporter(agent_host_name=settings.JAEGER_HOST_NAME, agent_port=settings.JAEGER_PORT)
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

    if settings.DEBUG:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))


async def require_header_request_id(x_request_id: Optional[str] = Header(default=None)):
    """Callback для проверки наличия в заголовке X-Request-Id для трассировки"""
    if x_request_id is None:
        if settings.DEBUG:
            pass
        else:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="X-Request-Id header id is required")
