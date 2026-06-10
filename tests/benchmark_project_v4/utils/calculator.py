# BUG-1 传播点: TAX_RATE 是字符串，float(TAX_RATE) * price 在运行时 TypeError
# BUG-3: apply_platform_fee 内部调用了不存在的 get_fee_rate()
from config.settings import TAX_RATE, DISCOUNT_THRESHOLD, PLATFORM_FEE_RATE


def calculate_tax(price: float) -> float:
    return float(TAX_RATE) * price


def calculate_discount(price: float) -> float:
    if price >= DISCOUNT_THRESHOLD:
        return price * 0.1
    return 0.0


def calculate_shipping(price: float, free_threshold: float) -> float:
    if price >= free_threshold:
        return 0.0
    return 15.0


def apply_platform_fee(subtotal: float) -> float:
    # BUG-3: get_fee_rate() 不存在，应直接用 PLATFORM_FEE_RATE
    fee = get_fee_rate() * subtotal
    return subtotal + fee


def calculate_total(price: float, quantity: int) -> float:
    subtotal = price * quantity
    tax = calculate_tax(subtotal)
    discount = calculate_discount(subtotal)
    return subtotal + tax - discount