# 修复：bulk_save_orders → 逐个调用 save_order
from repository.order_repository import save_order
from services.pricing_service import compute_order_price
from utils.validator import validate_order
from config.logger import logger


def process_batch_orders(orders: list) -> dict:
    results = {"success": [], "failed": []}
    valid_orders = []

    for order in orders:
        try:
            validate_order(order)
            order.total_amount = compute_order_price(order)
            valid_orders.append(order)
        except Exception as e:
            results["failed"].append({"order_id": order.order_id, "reason": str(e)})

    if valid_orders:
        for order in valid_orders:
            save_order(order)
        results["success"] = [o.order_id for o in valid_orders]
        logger.info(f"Batch saved {len(valid_orders)} orders")

    return results


def compute_batch_totals(orders: list) -> float:
    return sum(compute_order_price(o) for o in orders)