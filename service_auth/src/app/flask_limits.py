from flask import Flask, current_app
from flask_limiter import Limiter

from app.core.utils import limit_by_ip_key, limit_by_user_id_key

# для декорирования ендпойнтов нужно, чтобы экземпляр класса Limiter существовал во время импорта
# модулей с ендпойнтами, поэтому сохраняем ссылку на экземпляр в этом модуле
limiter = Limiter(limit_by_user_id_key)

limit_by_user_id = limiter.limit(lambda: current_app.config["RATE_LIMIT"])
limit_by_ip = limiter.limit(lambda: current_app.config["RATE_LIMIT"], key_func=limit_by_ip_key)


def init_limiter(app: Flask):
    limiter.init_app(app)
