# BUG-6: inventory_service 调用了 find_by_id()，但此处只定义了 get_product()
from config.logger import logger

_product_store = {}


def save_product(product) -> None:
    _product_store[product.product_id] = product
    logger.info(f"Saved product {product.product_id}")


def get_product(product_id: str):
    product = _product_store.get(product_id)
    if not product:
        raise KeyError(f"Product not found: {product_id}")
    return product


def list_products() -> list:
    return list(_product_store.values())


def delete_product(product_id: str) -> None:
    if product_id not in _product_store:
        raise KeyError(f"Product not found: {product_id}")
    del _product_store[product_id]
    logger.info(f"Deleted product {product_id}")


def update_stock(product_id: str, new_stock: int) -> None:
    product = get_product(product_id)
    product.stock = new_stock
    logger.info(f"Updated stock for {product_id}: {new_stock}")