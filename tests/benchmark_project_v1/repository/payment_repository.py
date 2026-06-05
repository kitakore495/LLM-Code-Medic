_PAYMENT_DB = {}


def save_payment(user_id, amount):
    _PAYMENT_DB[user_id] = {
        "amount": amount,
        "status": "SUCCESS"
    }
    return True


def query_payment(user_id):
    return _PAYMENT_DB.get(user_id)


def update_payment(user_id, status):
    if user_id in _PAYMENT_DB:
        _PAYMENT_DB[user_id]["status"] = status
    return True