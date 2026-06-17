# BUG-4: import 了不存在的 MAX_RETRY_COUNT（settings 里是 MAX_RETRIES）
from config.settings import MAX_RETRY_COUNT   # BUG-4: should be MAX_RETRIES


def validate_product(product) -> bool:
    if not product:
        raise ValueError("Product cannot be None")
    if product.price <= 0:
        raise ValueError(f"Invalid price: {product.price}")
    if product.stock < 0:
        raise ValueError(f"Invalid stock: {product.stock}")
    return True


def validate_order(order) -> bool:
    if not order:
        raise ValueError("Order cannot be None")
    if not order.items:
        raise ValueError("Order must have at least one item")
    if not order.user_id:
        raise ValueError("Order must have a user_id")
    return True


def validate_quantity(quantity: int) -> bool:
    if quantity <= 0:
        raise ValueError(f"Quantity must be positive, got {quantity}")
    if quantity > MAX_RETRY_COUNT * 100:
        raise ValueError(f"Quantity {quantity} exceeds limit")
    return True