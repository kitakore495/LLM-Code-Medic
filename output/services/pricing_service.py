# BUG-1 传播: calculate_tax 使用字符串 TAX_RATE，触发 TypeError
# BUG-7: apply_platform_fee 内部调用不存在的 get_fee_rate()
from utils.calculator import calculate_tax, calculate_discount, apply_platform_fee
from config.logger import logger


def compute_item_price(unit_price: float, quantity: int) -> float:
    subtotal = unit_price * quantity
    tax = calculate_tax(subtotal)         # BUG-1 传播
    discount = calculate_discount(subtotal)
    return subtotal + tax - discount


def compute_order_price(order) -> float:
    total = 0.0
    for item in order.items:
        item_total = compute_item_price(item["unit_price"], item["quantity"])
        total += item_total
    total_with_fee = apply_platform_fee(total)   # BUG-7
    logger.info(f"Computed order price: {total_with_fee:.2f}")
    return total_with_fee


def estimate_shipping(order_total: float) -> float:
    from config.settings import FREE_SHIPPING_THRESHOLD
    from utils.calculator import calculate_shipping
    return calculate_shipping(order_total, FREE_SHIPPING_THRESHOLD)