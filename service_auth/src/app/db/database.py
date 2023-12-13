import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from http import HTTPStatus
from uuid import UUID

from pydantic import BaseModel
from werkzeug.security import check_password_hash, generate_password_hash

import app.models.db_models as data
from app.core.utils import error

UserID = UUID


class DatabaseError(Exception):
    pass


class NotFoundUser(DatabaseError):
    pass


class UserAddError(DatabaseError):
    pass


class UserChangeError(DatabaseError):
    pass


class Role(BaseModel):
    id: UUID
    name: str

    @classmethod
    def from_db(cls, db_role: data.Role):
        return cls(id=db_role.id, name=db_role.name)


class UserInfo(BaseModel):
    user_id: UserID
    email: str | None
    phone: str | None
    username: str
    time_zone: str = "UTC"
    reject_notice: list[str]

    @classmethod
    def from_db(cls, db_user: data.User):
        return cls(
            user_id=db_user.id,
            email=db_user.email,
            phone=db_user.phone,
            username=db_user.username,
            time_zone=db_user.time_zone,
            reject_notice=db_user.reject_notice or [],
        )


class User(BaseModel):
    id: UserID
    login: str
    password_hash: str
    name: str
    registered: datetime
    is_confirmed: bool
    is_root: bool
    roles: list[Role]

    def roles_list(self) -> list[str]:
        return [role.name for role in self.roles]

    @classmethod
    def from_db(cls, db_user: data.User):
        return cls(
            id=db_user.id,
            login=db_user.email,
            password_hash=db_user.password_hash,
            name=db_user.username,
            registered=db_user.registered_on,
            is_confirmed=db_user.is_confirmed,
            is_root=db_user.is_root,
            roles=[Role.from_db(db_role) for db_role in db_user.roles],
        )


class UserSession(BaseModel):
    id: UUID
    user_id: UUID
    device_name: str
    device_id: str
    remote_ip: str

    @classmethod
    def from_db(cls, db_session: data.UserSession):
        return cls(
            id=db_session.id,
            user_id=db_session.user_id,
            device_name=db_session.device_name,
            device_id=db_session.device_id,
            remote_ip=db_session.remote_ip,
        )


class UserAction(BaseModel):
    id: UUID
    device_name: str
    timestamp: datetime
    action: str

    @classmethod
    def from_db(cls, db_user_action: data.UserAction):
        return cls(
            id=db_user_action.id,
            device_name=db_user_action.device_name,
            timestamp=db_user_action.action_time,
            action=db_user_action.action_type,
        )


class UserSocial(BaseModel):
    id: UUID
    social_user_id: str
    social_name: str

    @classmethod
    def from_db(cls, db_user_social: data.UserSocial):
        return cls(
            id=db_user_social.id,
            social_user_id=db_user_social.social_net_user_id,
            social_name=db_user_social.social_net_name,
        )


# YAGNI
class AbstractUsers(ABC):
    @abstractmethod
    def add_user(self, login, password, name, registered=datetime.now(tz=timezone.utc)) -> User:
        pass

    @abstractmethod
    def change_user_login(self, user_id: UserID, new_login: str) -> User:
        pass

    @abstractmethod
    def change_user_password(self, user_id: UserID, new_password: str) -> User:
        pass

    @abstractmethod
    def change_user_name(self, user_id: UserID, new_name: str) -> User:
        pass

    @abstractmethod
    def change_user(self, user_id: UserID, new_name: str, new_password: str) -> User:
        pass

    @abstractmethod
    def is_user_exists(self, login: str) -> bool:
        pass

    @abstractmethod
    def auth_user(self, login: str, password: str) -> User | None:
        pass

    @abstractmethod
    def user_by_login(self, login: str) -> User | None:
        pass

    @abstractmethod
    def user_by_id(self, user_id: UserID) -> User | None:
        pass

    @abstractmethod
    def users_info(self, user_ids: list[UserID]) -> list[UserInfo]:
        pass


class AbstractRoles(ABC):
    @abstractmethod
    def get_all_roles(self) -> list[Role]:
        pass

    @abstractmethod
    def add_role(self, name: str) -> Role:
        pass

    @abstractmethod
    def is_role_exists(self, name: str) -> bool:
        pass

    @abstractmethod
    def get_role_by_name(self, name: str) -> Role | None:
        pass

    @abstractmethod
    def delete_role(self, role_id: UUID) -> bool:
        pass

    @abstractmethod
    def update_role(self, role_id: UUID, new_name: str) -> Role | None:
        pass

    @abstractmethod
    def role_by_id(self, role_id: UUID) -> Role | None:
        pass

    @abstractmethod
    def get_user_roles(self, user_id: UserID) -> list[Role | None]:
        pass

    @abstractmethod
    def add_user_role(self, user_id: UserID, role_id: UUID) -> list[Role] | None:
        pass

    @abstractmethod
    def delete_user_role(self, user_id: UserID, role_id: UUID):
        pass


class AbstractActions(ABC):
    @abstractmethod
    def add_user_action(self, user_id: UserID, device_name: str, action: str) -> UserAction:
        pass

    @abstractmethod
    def get_user_actions(self, user_id: UserID, days_limit=30) -> list[UserAction | None]:
        pass


class AbstractSocialAccounts(ABC):
    @abstractmethod
    def add_social(self, user_id: UserID, social_id: str, social_name: str) -> UUID:
        """add record to socials"""
        pass

    @abstractmethod
    def user_by_social(self, social_id: str, social_name: str) -> UserID | None:
        """find user by his social_id and social_name if exists"""
        pass

    @abstractmethod
    def get_user_socials(self, user_id: UserID) -> list[UserSocial]:
        pass

    @abstractmethod
    def delete_user_social(self, user_id: UserID, social_id: UUID) -> list[UserSocial]:
        pass


class Users(AbstractUsers):
    def add_user(self, login, password, name, registered=datetime.now(tz=timezone.utc)) -> User:
        """
        Добавляем пользователя в базу
        Если не задано имя, но есть логин(email) используем в качестве имени email
        Если нет ни имени, не email, то имя устанавливаем в Anonymous, логин(email) в user_id

        """
        hash_password = generate_password_hash(password)

        if not name:
            if login:
                name = login
            else:
                name = "Anonymous"

        user_id = uuid.uuid4()

        if not login:
            login = str(user_id)
        db_user = data.User(
            id=user_id, email=login, password_hash=hash_password, username=name, registered_on=registered
        )

        data.db.session.add(db_user)
        data.db.session.commit()
        return User.from_db(db_user)

    def change_user_login(self, user_id: UserID, new_login: str) -> User:
        db_user = data.User.find_by_id(user_id)

        if new_login == db_user.email:
            return User.from_db(db_user)

        if self.is_user_exists(new_login):
            error("user with this login already exists", HTTPStatus.CONFLICT)

        db_user.email = new_login
        data.db.session.add(db_user)
        data.db.session.commit()
        return User.from_db(db_user)

    def change_user_password(self, user_id: UserID, new_password: str) -> User:
        db_user = data.User.find_by_id(user_id)

        hash_password = generate_password_hash(new_password)
        db_user.password_hash = hash_password
        data.db.session.add(db_user)
        data.db.session.commit()
        return User.from_db(db_user)

    def change_user_name(self, user_id: UserID, new_name: str) -> User:
        db_user = data.User.find_by_id(user_id)
        db_user.username = new_name
        data.db.session.add(db_user)
        data.db.session.commit()
        return User.from_db(db_user)

    def change_user(self, user_id: UserID, new_name: str | None, new_password: str | None) -> User:
        db_user = data.User.find_by_id(user_id)
        if not new_name and not new_password:
            return User.from_db(db_user)

        if new_name:
            db_user.username = new_name

        if new_password:
            hash_password = generate_password_hash(new_password)
            db_user.password_hash = hash_password

        data.db.session.add(db_user)
        data.db.session.commit()
        return User.from_db(db_user)

    def is_user_exists(self, login: str) -> bool:
        return data.User.find_by_email(login)

    def auth_user(self, login: str, password: str) -> User | None:
        """проводит аутентификацию пользователя"""
        user = self.user_by_login(login)
        if not user or not check_password_hash(user.password_hash, password):
            return None
        return user

    def user_by_login(self, login: str) -> User | None:
        db_user: data.User = data.User.find_by_email(login)
        if not db_user:
            return None
        else:
            return User.from_db(db_user)

    def user_by_id(self, user_id: UserID) -> User | None:
        db_user: data.User = data.User.find_by_id(user_id)
        if db_user is None:
            return None

        return User.from_db(db_user)

    def users_info(self, user_ids: list[UserID]) -> list[UserInfo]:
        db_users = data.User.query.filter(data.User.id.in_(user_ids))
        return [UserInfo.from_db(db_user) for db_user in db_users]


class Roles(AbstractRoles):
    def get_all_roles(self) -> list[Role]:
        query = data.Role.query.all()
        roles = [Role.from_db(db_role) for db_role in query]
        return roles

    def add_role(self, name: str) -> Role:
        db_role = data.Role(name=name)
        data.db.session.add(db_role)
        data.db.session.commit()
        return Role.from_db(db_role)

    def is_role_exists(self, name: str) -> bool:
        return bool(data.Role.find_by_name(name))

    def get_role_by_name(self, name: str) -> Role | None:
        db_role = data.Role.find_by_name(name)
        if not db_role:
            return None
        return Role.from_db(db_role)

    def delete_role(self, role_id: UUID) -> bool:
        if data.Role.find_by_id(role_id) is None:
            return False

        data.Role.query.filter_by(id=role_id).delete()
        data.db.session.commit()
        return True

    def update_role(self, role_id: UUID, new_name: str) -> Role | None:
        if (db_role := data.Role.find_by_id(role_id)) is None:
            return None

        db_role.name = new_name
        data.db.session.commit()
        return Role.from_db(db_role)

    def role_by_id(self, role_id: UUID) -> Role | None:
        if (db_role := data.Role.find_by_id(role_id)) is None:
            return None
        return Role.from_db(db_role)

    def get_user_roles(self, user_id: UserID) -> list[Role | None]:
        query = data.User.find_by_id(user_id).roles
        roles = [Role.from_db(db_role) for db_role in query]
        return roles

    def add_user_role(self, user_id: UserID, role_id: UUID) -> list[Role] | None:
        role = data.Role.query.filter_by(id=role_id).first()
        if role is None:
            return None
        user = data.User.find_by_id(user_id)
        if user is None:
            return None
        user.roles.append(role)
        data.db.session.commit()
        return [Role.from_db(db_role) for db_role in user.roles]

    def delete_user_role(self, user_id: UserID, role_id: UUID):
        role = data.Role.query.filter_by(id=role_id).first()
        if role is None:
            return None
        user = data.User.find_by_id(user_id)
        if user is None:
            return None
        user.roles.remove(role)
        data.db.session.commit()
        return [Role.from_db(db_role) for db_role in user.roles]


class Actions(AbstractActions):
    def add_user_action(self, user_id: UserID, device_name: str, action: str) -> UserAction:
        db_user_action = data.UserAction(user_id=user_id, device_name=device_name, action_type=action)
        data.db.session.add(db_user_action)
        data.db.session.commit()
        return UserAction.from_db(db_user_action)

    def get_user_actions(self, user_id: UserID, days_limit=30) -> list[UserAction | None]:
        actions = data.UserAction.by_user_id(user_id, days_limit=30)
        result = [UserAction.from_db(db_action) for db_action in actions]
        return result


class SocialAccounts(AbstractSocialAccounts):
    def user_by_social(self, social_id: str, social_name: str) -> UserID | None:
        db_social: data.UserSocial = data.UserSocial.get_user_by_social(social_id, social_name)
        if not db_social:
            return None
        user_id: UserID = db_social.user_id
        return user_id

    def add_social(self, user_id: UserID, social_id: str, social_name: str) -> UUID:
        db_social = data.UserSocial(user_id=user_id, social_net_name=social_name, social_net_user_id=social_id)
        data.db.session.add(db_social)
        data.db.session.commit()
        return db_social.id

    def get_user_socials(self, user_id: UserID) -> list[UserSocial]:
        db_socials = data.UserSocial.by_user_id(user_id)
        result = [UserSocial.from_db(db_social) for db_social in db_socials]
        return result

    def delete_user_social(self, user_id: UserID, social_id: UUID) -> list[UserSocial] | None:
        user: data.User = data.User.find_by_id(user_id)
        if user is None:
            return None
        social: data.UserSocial = data.UserSocial.query.get(social_id)
        if social is None:
            return None
        data.db.session.delete(social)
        data.db.session.commit()
        result = [UserSocial.from_db(db_social) for db_social in user.social_accounts]
        return result
