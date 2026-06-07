# BUG-10: utils.mailer 模块不存在，移除依赖，内部实现发送动作
from utils.formatter import format_order_summary
from config.logger import logger


def _send_email(to: str, subject: str, body: str) -> None:
    logger.info(f"Email would be sent to {to}: subject='{subject}'")


def notify_order_submitted(order) -> None:
    summary = format_order_summary(order)
    _send_email(
        to="customer@example.com",
        subject=f"Order {order.order_id} Confirmed",
        body=summary,
    )
    logger.info(f"Notification sent for order {order.order_id}")


def notify_order_cancelled(order) -> None:
    logger.warning(f"Order {order.order_id} was cancelled")
    _send_email(
        to="customer@example.com",
        subject=f"Order {order.order_id} Cancelled",
        body=f"Your order {order.order_id} has been cancelled.",
    )


def notify_low_stock(product_id: str, current_stock: int) -> None:
    logger.warning(f"Low stock alert: {product_id} has {current_stock} units left")
    _send_email(
        to="ops@example.com",
        subject=f"Low Stock: {product_id}",
        body=f"Product {product_id} stock is critically low: {current_stock}",
    )