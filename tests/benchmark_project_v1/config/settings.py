DB_HOST = "127.0.0.1"

DB_PORT = 3306

PAYMENT_TIMEOUT = 10

EMAIL_SENDER = "system@test.com"

DEFAULT_TAX = 0.13

DEFAULT_DISCOUNT = 0.05


def get_database_url():

    return f"{DB_HOST}:{DB_PORT}"


def get_tax():

    return DEFAULT_TAX


def get_discount():

    return DEFAULT_DISCOUNT