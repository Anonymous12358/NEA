import peewee

from pente.account.accounts import Account

_WIN_REASON_CHAR_LIMIT = 63
db = peewee.SqliteDatabase('resources/account.db')


class Wins(peewee.Model):
    id = peewee.ForeignKeyField(Account)
    win_reason = peewee.CharField(max_length=_WIN_REASON_CHAR_LIMIT)
    wins = peewee.IntegerField()

    class Meta:
        database = db
        primary_key = peewee.CompositeKey('id', 'win_reason')


# A:cross-table-sql
# Use SQL to interact with the database when a player wins a game or requests the statistics
# Note that the strings for the queries are constructed in the peewee library, based on Python objects
# Delegating the construction of queries to a well-tested library better protects against SQL injection
# The Wins table refers to users by their UUID rather than name, so queries are cross-table to provide access to records
# by account name
def get_wins(username: str, win_reason: str) -> int:
    query = Wins.select().join(Account).where(Account.username == username, Wins.win_reason == win_reason)
    if not query.exists():
        return 0
    return query.get().wins


def get_all_wins(username: str) -> dict[str, int]:
    query = Wins.select().join(Account).where(Account.username == username)
    return {record.win_reason: record.wins for record in query}


def set_wins(username: str, win_reason: str, wins: int) -> bool:
    if len(win_reason) > _WIN_REASON_CHAR_LIMIT:
        return False

    query = Wins.select().join(Account).where(Account.username == username, Wins.win_reason == win_reason)
    if not query.exists():
        user_id = Account.get(Account.username == username)
        Wins.create(id=user_id, win_reason=win_reason, wins=wins)
    else:
        record = query.get()
        record.wins = wins
        record.save()


def clear_wins(username: str):
    user_id = Account.get(Account.username == username)
    Wins.delete().where(Wins.id == user_id).execute()
