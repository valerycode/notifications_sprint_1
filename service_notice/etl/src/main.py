import logging

import db.pg as db_pg
import db.rmq as db_rmq
import db.storage as db_redis
from core import logging_config  # noqa
from core.config import settings
from core.etl import ETL
from core.tracer import init_tracer


def set_quit_signal(callback):
    """Ловим сигналы на закрытие"""
    import signal

    for sig in ("TERM", "HUP", "INT"):
        signal.signal(getattr(signal, "SIG" + sig), callback)


def init_db():
    logging.info("Init DB...")
    # все подключения под backoff в классах
    db_rmq.db = db_rmq.RabbitMQ(settings.RABBITMQ_URI)
    db_pg.db = db_pg.PostgresDB(settings.PG_URI)
    db_redis.db = db_redis.Storage(settings.REDIS_URI)


def close_db():
    db_rmq.db.close()
    db_pg.db.close()
    db_redis.db.close()


def main():
    init_db()

    if settings.ENABLE_TRACER:
        init_tracer()

    def on_quit(sig_no: int, *args):
        etl.stop()

    logging.info("start notice etl")
    etl = ETL(db_rmq.db)
    set_quit_signal(on_quit)
    etl.run()
    logging.info("stop notice etl")

    close_db()


if __name__ == "__main__":
    main()
