from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from core.config import settings


def init_tracer():
    provider = TracerProvider(resource=Resource.create({"service.name": settings.PROJECT_NAME}))
    # Sets the global default tracer provider
    trace.set_tracer_provider(provider)

    jaeger_exporter = JaegerExporter(agent_host_name=settings.JAEGER_HOST_NAME, agent_port=settings.JAEGER_PORT)
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
