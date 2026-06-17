# BUG-8: save_order(order, order.user_id) 多传了参数，save_order 只接受 (order)
from repository.order_repository import save_order, get_order, update_order
from services.pricing_service import compute_order_price, estimate_shipping
from services.inventory_service import get_product_info, check_availability
from utils.validator import validate_order, validate_quantity
from config.logger import logger


def submit_order(order) -> dict:
    validate_order(order)

    for item in order.items:
        validate_quantity(item["quantity"])
        if not check_availability(item["product_id"], item["quantity"]):
            raise ValueError(f"Product {item['product_id']} has insufficient stock")

    order.total_amount = compute_order_price(order)
    shipping = estimate_shipping(order.total_amount)

    # BUG-8: save_order 只接受 (order)，多传了 user_id
    save_order(order, order.user_id)

    logger.info(f"Order {order.order_id} submitted, total={order.total_amount:.2f}")
    return {
        "order_id": order.order_id,
        "total": order.total_amount,
        "shipping": shipping,
        "status": order.status,
    }


def cancel_order(order_id: str) -> None:
    order = get_order(order_id)
    order.mark_cancelled()
    update_order(order)
    logger.info(f"Order {order_id} cancelled")


def get_order_detail(order_id: str) -> dict:
    order = get_order(order_id)
    return order.to_dict()