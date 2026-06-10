from config.logger import logger

_order_store = {}


def save_order(order) -> None:
    _order_store[order.order_id] = order
    logger.info(f"Saved order {order.order_id}")


def get_order(order_id: str):
    order = _order_store.get(order_id)
    if not order:
        raise KeyError(f"Order not found: {order_id}")
    return order


def list_orders_by_user(user_id: str) -> list:
    return [o for o in _order_store.values() if o.user_id == user_id]


def update_order(order) -> None:
    if order.order_id not in _order_store:
        raise KeyError(f"Order not found: {order.order_id}")
    _order_store[order.order_id] = order
    logger.info(f"Updated order {order.order_id}")


def delete_order(order_id: str) -> None:
    if order_id not in _order_store:
        raise KeyError(f"Order not found: {order_id}")
    del _order_store[order_id]
    logger.info(f"Deleted order {order_id}")