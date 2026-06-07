# BUG-11: process_order 不存在，应为 submit_order
from services.order_service import submit_order
from services.notification_service import notify_order_submitted
from services.report_service import generate_user_report
from services.inventory_service import list_low_stock
from config.logger import logger


def run_order_pipeline(order) -> dict:
    logger.info(f"Starting order pipeline for {order.order_id}")

    result = submit_order(order)

    try:
        notify_order_submitted(order)
    except Exception as e:
        logger.warning(f"Notification failed (non-fatal): {e}")

    low_stock = list_low_stock(threshold=5)
    if low_stock:
        logger.warning(f"Low stock items: {[p.product_id for p in low_stock]}")

    return result


def run_report_pipeline(user_id: str) -> str:
    logger.info(f"Generating report for user {user_id}")
    return generate_user_report(user_id)