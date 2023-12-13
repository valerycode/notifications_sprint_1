import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship

from app.flask_db import db


def now_with_tz_info():
    return datetime.now(tz=timezone.utc)


class Role(db.Model):
    # root, admin, subscriber, user, reviewer, etc
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(255), nullable=False, unique=True)

    def __repr__(self):
        return self.name

    @classmethod
    def find_by_name(cls, name):
        query = cls.query.filter_by(name=name).first()
        return query

    @classmethod
    def find_by_id(cls, role_id):
        query = cls.query.filter_by(id=role_id).first()
        return query


user_roles = db.Table(
    "user_roles",
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE")),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")),
)
# set (user_id, role_id) is unique!
Index("idx_user_role", user_roles.c.user_id, user_roles.c.role_id, unique=True)


class User(db.Model):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    username = Column(String(255))
    phone = Column(String(50))
    reject_notice = Column(JSONB, default=list)
    time_zone = Column(String(50), default="UTC")
    registered_on = Column(DateTime(timezone=True), default=now_with_tz_info, nullable=False)
    # subscribe_expiration
    is_confirmed = Column(Boolean, default=False)
    is_root = Column(Boolean, default=False)
    roles = relationship("Role", secondary=user_roles, lazy="subquery", backref=backref("users", lazy=True))

    @classmethod
    def find_by_email(cls, email):
        query = cls.query.filter_by(email=email).first()
        return query

    @classmethod
    def find_by_id(cls, user_id):
        query = cls.query.filter_by(id=user_id).first()
        return query


def create_user_actions_partitions(target, connection, **kw) -> None:
    connection.execute(
        """CREATE TABLE user_actions_0 PARTITION OF user_actions FOR VALUES WITH (MODULUS 3,REMAINDER 0)"""
    )
    connection.execute(
        """CREATE TABLE user_actions_1 PARTITION OF user_actions FOR VALUES WITH (MODULUS 3,REMAINDER 1)"""
    )
    connection.execute(
        """CREATE TABLE user_actions_2 PARTITION OF user_actions FOR VALUES WITH (MODULUS 3,REMAINDER 2)"""
    )


class UserAction(db.Model):
    __tablename__ = "user_actions"
    __table_args__ = (
        UniqueConstraint("id", "user_id"),
        {
            "postgresql_partition_by": "HASH (user_id)",
            "listeners": [("after_create", create_user_actions_partitions)],
        },
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    device_name = Column(String(255))
    action_type = Column(String(255))
    action_time = Column(DateTime(timezone=True), default=now_with_tz_info)

    @classmethod
    def by_user_id(cls, user_id, days_limit=30):
        start_time = datetime.now() - timedelta(days=days_limit)
        query = cls.query.filter_by(user_id=user_id).filter(cls.action_time > start_time)
        return query


# !!!! its for future usage
class UserSession(db.Model):
    __tablename__ = "user_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    device_id = Column(String(100))  # hash sha256
    device_name = Column(String(255))  # user_agent or another device name
    remote_ip = Column(String(45))  # client ip
    login_at = Column(DateTime(timezone=True), default=now_with_tz_info)  # first sign
    active_at = Column(DateTime(timezone=True), default=now_with_tz_info)  # every refresh updated
    logout_at = Column(DateTime(timezone=True), default=None)  # when logout
    # life time of refresh token, active_at+JWT_REFRESH_TOKEN_EXPIRES
    active_till = Column(DateTime(timezone=True), default=None)

    @classmethod
    def by_user_id(cls, user_id, active=True):
        # TODO return active sessions
        query = cls.query.filter_by(user_id=user_id)
        return query


class UserSocial(db.Model):
    __tablename__ = "social_account"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    social_net_user_id = db.Column(String(255), nullable=False)
    social_net_name = db.Column(String(255), nullable=False)

    user = db.relationship("User", backref=backref("social_accounts", lazy="select"), uselist=False)
    __table_args__ = (db.UniqueConstraint("social_net_user_id", "social_net_name", name="social_pk"),)

    @classmethod
    def get_user_by_social(cls, social_net_user_id, social_net_name):
        query = cls.query.filter_by(social_net_user_id=social_net_user_id, social_net_name=social_net_name).first()
        return query

    @classmethod
    def by_user_id(cls, user_id):
        query = cls.query.filter_by(user_id=user_id)
        return query
