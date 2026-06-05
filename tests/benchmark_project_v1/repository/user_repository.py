# Bug #3 已修复：将原错误的 DATABASE_HOST 更正为真实配置 DB_HOST
from config.settings import DB_HOST

_USER_DB = {
    1001: {
        "name": "Alice",
        "email": "alice@test.com"
    },
    1002: {
        "name": "Bob",
        "email": "bob@test.com"
    }
}


def get_user(user_id):
    return _USER_DB.get(user_id)


def get_database_host():
    return DB_HOST


def user_exists(user_id):
    return user_id in _USER_DB