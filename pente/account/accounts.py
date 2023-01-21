import hashlib
import secrets
import uuid
from typing import Optional

import peewee

db = peewee.SqliteDatabase('resources/account.db')


class Account(peewee.Model):
    id = peewee.UUIDField(primary_key=True)
    username = peewee.CharField(max_length=31)
    salt = peewee.BlobField()
    hash = peewee.BlobField()
    # The payload for the ANSI escape to set the color
    color = peewee.CharField(max_length=31)

    class Meta:
        database = db


#########################################################################################################
# SECTION B SKILL: SINGLE-TABLE SQL                                                                     #
# Use SQL to interact with the database when a user registers, logs in or out, or changes details       #
# Note that the strings for the queries are constructed in the peewee library, based on Python objects  #
# Delegating the construction of queries to a well-tested library better protects against SQL injection #
#########################################################################################################
def register(username: str, password: str) -> Optional[uuid.UUID]:
    if Account.select().where(Account.username == username).exists():
        return None

    user_id = uuid.uuid4()
    while Account.select().where(Account.id == user_id).exists():
        user_id = uuid.uuid4()

    salt = secrets.token_bytes(8)
    hash_ = hashlib.sha256(bytes(password, 'utf-8') + salt).digest()

    Account.create(id=user_id, username=username, salt=salt, hash=hash_, color='0')
    return user_id


def login(username: str, password: str) -> bool:
    if not Account.select().where(Account.username == username).exists():
        return False

    account = Account.get(Account.username == username)
    salt = account.salt

    hash_ = hashlib.sha256(bytes(password, 'utf-8') + salt).digest()
    return hash_ == account.hash


def delete(username: str):
    Account.delete().where(Account.username == username).execute()


def get_color(username: str) -> str:
    account = Account.get(Account.username == username)
    return account.color


def set_color(username: str, color: str):
    account = Account.get(Account.username == username)
    account.color = color
    account.save()
