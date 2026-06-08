import os
from utils.formatter import format_curency, format_order_summary
from repository.order_repository import list_orders_by_user
from config.settings import REPORT_OUTPUT_DIR
from config.logger import logger


def generate_user_report(user_id: str) -> str:
    orders = list_orders_by_user(user_id)
    if not orders:
        return f"No orders found for user {user_id}"

    lines = [f"=== Order Report for User {user_id} ==="]
    total_spent = 0.0

    for order in orders:
        lines.append(format_order_summary(order))
        total_spent += order.total_amount

    lines.append(f"\nTotal spent: {format_curency(total_spent)}")
    return "\n".join(lines)


def save_report_to_file(user_id: str, content: str) -> str:
    os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
    file_path = os.path.join(REPORT_OUTPUT_DIR, f"report_{user_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Report saved to {file_path}")
    return file_path