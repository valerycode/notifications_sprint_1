from gevent import monkey

monkey.patch_all()

from app import create_app
from config import flask_config

app = create_app(flask_config)
