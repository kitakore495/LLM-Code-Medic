from datetime import datetime


class Product:
    def __init__(self, product_id: str, name: str, price: float, stock: int):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.stock = stock
        self.created_at = datetime.now()

    def is_available(self) -> bool:
        return self.stock > 0

    def reduce_stock(self, quantity: int):
        if quantity > self.stock:
            raise ValueError(
                f"Insufficient stock for {self.product_id}: "
                f"requested={quantity}, available={self.stock}"
            )
        self.stock -= quantity

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
        }