from utils.calculator import calculate_tax, calculate_discount, apply_platform_fee, calculate_shipping
from config.settings import FREE_SHIPPING_THRESHOLD
from config.logger import logger


def compute_item_price(unit_price: float, quantity: int) -> float:
    """计算单个商品种类的小计（含税、折扣）。"""
    subtotal = unit_price * quantity
    tax = calculate_tax(subtotal)
    discount = calculate_discount(subtotal)
    return subtotal + tax - discount


def compute_order_price(order) -> float:
    """计算整个订单的总金额（含平台费）。"""
    total = 0.0
    for item in order.items:
        item_total = compute_item_price(item["unit_price"], item["quantity"])
        total += item_total
    total_with_fee = apply_platform_fee(total)
    logger.info(f"Computed order price: {total_with_fee:.2f}")
    return total_with_fee


def estimate_shipping(order_total: float) -> float:
    """根据订单总金额估算运费。"""
    return calculate_shipping(order_total, FREE_SHIPPING_THRESHOLD)