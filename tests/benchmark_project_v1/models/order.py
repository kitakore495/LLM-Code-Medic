class Order:

    def __init__(self, user_id, product, price):
        self.user_id = user_id
        self.product = product
        self.price = price
        self.status = "CREATED"
        self.amount = price

    def mark_paid(self):
        self.status = "PAID"

    def mark_cancelled(self):
        self.status = "CANCELLED"

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "product": self.product,
            "price": self.price,
            "amount": self.amount,
            "status": self.status
        }