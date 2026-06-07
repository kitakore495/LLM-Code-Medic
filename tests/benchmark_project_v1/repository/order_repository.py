from config.logger import logger

_ORDER_DB = {}


def save_order(order):
    _ORDER_DB[order.user_id] = order
    logger.info(f"save order {order.user_id}")
    return True


def query_order(user_id):
    return _ORDER_DB.get(user_id)


def update_order(order):
    _ORDER_DB[order.user_id] = order
    return True


def delete_order(user_id):
    if user_id in _ORDER_DB:
        del _ORDER_DB[user_id]
    return True