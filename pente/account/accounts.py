import hashlib
import secrets
import uuid
from typing import Optional

import peewee

db = peewee.SqliteDatabase('resources/account.db')


class _Account(peewee.Model):
    id = peewee.UUIDField(primary_key=True)
    username = peewee.CharField(max_length=31)
    salt = peewee.BlobField()
    hash_ = peewee.BlobField()
    # The payload for the ANSI escape to set the color
    color = peewee.CharField(max_length=31)

    class Meta:
        database = db


def register(username: str, password: str) -> Optional[uuid.UUID]:
    if _Account.select().where(_Account.username == username).exists():
        return None

    user_id = uuid.uuid4()
    while _Account.select().where(_Account.id == user_id).exists():
        user_id = uuid.uuid4()

    salt = secrets.token_bytes(8)
    hash_ = hashlib.sha256(bytes(password, 'utf-8') + salt).digest()

    _Account.create(id=user_id, username=username, salt=salt, hash_=hash_, color='0')
    return user_id


def login(username: str, password: str) -> bool:
    if not _Account.select().where(_Account.username == username).exists():
        return False

    account = _Account.get(_Account.username == username)
    salt = account.salt

    hash_ = hashlib.sha256(bytes(password, 'utf-8') + salt).digest()
    return hash_ == account.hash_


def delete(username: str):
    _Account.delete().where(_Account.username == username).execute()


def get_color(username: str) -> str:
    account = _Account.get(_Account.username == username)
    return account.color


def set_color(username: str, color: str):
    account = _Account.get(_Account.username == username)
    account.color = color
    account.save()
