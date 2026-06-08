from utils.formatter import format_order_summary
from config.logger import logger


def notify_order_submitted(order) -> None:
    summary = format_order_summary(order)
    logger.info(f"Notification for order {order.order_id}: {summary}")
    logger.info(f"Notification sent for order {order.order_id}")


def notify_order_cancelled(order) -> None:
    logger.warning(f"Order {order.order_id} was cancelled")
    logger.info(f"Notification for cancellation of order {order.order_id}")


def notify_low_stock(product_id: str, current_stock: int) -> None:
    logger.warning(f"Low stock alert: {product_id} has {current_stock} units left")
    logger.info(f"Notification sent for low stock: {product_id}")