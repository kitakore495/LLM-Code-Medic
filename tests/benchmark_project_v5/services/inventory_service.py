# BUG-6: 调用了 find_by_id()，product_repository 只有 get_product()
from repository.product_repository import find_by_id, save_product, update_stock  # BUG-6
from utils.validator import validate_product
from config.logger import logger


def get_product_info(product_id: str):
    product = find_by_id(product_id)   # BUG-6
    validate_product(product)
    return product


def restock_product(product_id: str, quantity: int) -> None:
    product = find_by_id(product_id)   # BUG-6
    old_stock = product.stock
    product.stock += quantity
    update_stock(product_id, product.stock)
    logger.info(f"Restocked {product_id}: {old_stock} -> {product.stock}")


def check_availability(product_id: str, required_quantity: int) -> bool:
    try:
        product = find_by_id(product_id)   # BUG-6
        return product.stock >= required_quantity
    except KeyError:
        return False


def list_low_stock(threshold: int = 10) -> list:
    from repository.product_repository import list_products
    products = list_products()
    return [p for p in products if p.stock <= threshold]