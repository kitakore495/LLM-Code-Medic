# BUG-10: utils.mailer 不存在，import 阶段直接 ModuleNotFoundError
from utils.mailer import send_email_raw    # BUG-10
from utils.formatter import format_order_summary
from config.logger import logger


def notify_order_submitted(order) -> None:
    summary = format_order_summary(order)
    send_email_raw(
        to="customer@example.com",
        subject=f"Order {order.order_id} Confirmed",
        body=summary,
    )
    logger.info(f"Notification sent for order {order.order_id}")


def notify_order_cancelled(order) -> None:
    logger.warning(f"Order {order.order_id} was cancelled")
    send_email_raw(
        to="customer@example.com",
        subject=f"Order {order.order_id} Cancelled",
        body=f"Your order {order.order_id} has been cancelled.",
    )


def notify_low_stock(product_id: str, current_stock: int) -> None:
    logger.warning(f"Low stock alert: {product_id} has {current_stock} units left")
    send_email_raw(
        to="ops@example.com",
        subject=f"Low Stock: {product_id}",
        body=f"Product {product_id} stock is critically low: {current_stock}",
    )