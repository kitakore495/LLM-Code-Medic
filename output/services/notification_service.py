# 修复：移除不存在的 utils.mailer 依赖；邮件发送替换为日志记录（保留函数结构，避免异常吞没）
from utils.formatter import format_order_summary
from config.logger import logger


def notify_order_submitted(order) -> None:
    summary = format_order_summary(order)
    logger.info(
        f"[mock-email] To customer@example.com, Subject: Order {order.order_id} Confirmed, Body: {summary}"
    )
    logger.info(f"Notification sent for order {order.order_id}")


def notify_order_cancelled(order) -> None:
    logger.warning(f"Order {order.order_id} was cancelled")
    logger.info(
        f"[mock-email] To customer@example.com, Subject: Order {order.order_id} Cancelled, Body: Your order has been cancelled."
    )


def notify_low_stock(product_id: str, current_stock: int) -> None:
    logger.warning(f"Low stock alert: {product_id} has {current_stock} units left")
    logger.info(
        f"[mock-email] To ops@example.com, Subject: Low Stock: {product_id}, Body: Product stock critically low: {current_stock}"
    )