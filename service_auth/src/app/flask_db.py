from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(flask_app: Flask):
    db.init_app(flask_app)
    return db
