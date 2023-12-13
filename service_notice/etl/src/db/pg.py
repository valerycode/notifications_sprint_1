import logging

import backoff
import psycopg2
from psycopg2.extensions import connection as PGConnection
from psycopg2.extras import DictCursor

CHECK_QUERY = """
SELECT id, subject, body
FROM public.templates limit 1;
"""


class PostgresDB:
    @backoff.on_exception(backoff.expo, psycopg2.OperationalError, max_time=60)
    def __init__(self, uri: str):
        logging.debug("start PostgreSQL")
        self.connection: PGConnection = psycopg2.connect(uri, cursor_factory=DictCursor)
        with self.connection.cursor() as cursor:
            cursor.execute(CHECK_QUERY)
            cursor.fetchall()
            logging.debug("check table templates")

    def execute_query(self, query: str) -> list[tuple]:
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return result

    def close(self):
        if self.connection:
            self.connection.close()
            logging.debug("close PostgreSQL")


db: PostgresDB | None = None


def get_template_from_db(template_id: str) -> tuple[str, str]:
    query = "select subject, body from public.templates where id='{0}'"
    result = db.execute_query(query.format(template_id))
    if result:
        return result[0]
    else:
        return "", ""
