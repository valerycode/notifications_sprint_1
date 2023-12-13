from uuid import UUID

from werkzeug.security import generate_password_hash

from app.flask_db import db
from app.models.db_models import User
from manage import app

uuids = [
    UUID("c3696fea-68d3-4de6-a854-0d101304d85d"),
    UUID("18e28a84-78bb-453b-8108-cf33c934fedb"),
    UUID("30d063a1-9289-4235-a78e-21d79afadfbc"),
    UUID("5ba55f12-94f2-45d9-8483-bd5dc4812e6e"),
    UUID("b7571439-33d3-4122-95f9-16d57e9d9265"),
]

timezones = [
    "Etc/GMT-12",
    "Etc/GMT-6",
    "Etc/GMT0",
    "Etc/GMT+6",
    "Etc/GMT+12",
]


def add_fake_data():
    with app.app_context():
        for i, (id_, tz) in enumerate(zip(uuids, timezones)):
            user = User(
                id=id_,
                email=f"test{i}@example.com",
                password_hash=generate_password_hash("password"),
                username=f"test{i}",
                phone="1234567890",
                reject_notice=[],
                time_zone=tz,
            )
            db.session.add(user)
        db.session.commit()


if __name__ == "__main__":
    add_fake_data()
