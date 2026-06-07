# BUG-6: find_by_id 不存在，改为 get_product
from repository.product_repository import get_product, save_product, update_stock
from utils.validator import validate_product
from config.logger import logger


def get_product_info(product_id: str):
    product = get_product(product_id)
    validate_product(product)
    return product


def restock_product(product_id: str, quantity: int) -> None:
    product = get_product(product_id)
    old_stock = product.stock
    product.stock += quantity
    update_stock(product_id, product.stock)
    logger.info(f"Restocked {product_id}: {old_stock} -> {product.stock}")


def check_availability(product_id: str, required_quantity: int) -> bool:
    try:
        product = get_product(product_id)
        return product.stock >= required_quantity
    except KeyError:
        return False


def list_low_stock(threshold: int = 10) -> list:
    from repository.product_repository import list_products
    products = list_products()
    return [p for p in products if p.stock <= threshold]