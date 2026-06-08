from datetime import datetime


class Order:
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_SHIPPED = "shipped"
    STATUS_CANCELLED = "cancelled"

    def __init__(self, order_id: str, user_id: str, items: list):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.status = self.STATUS_PENDING
        self.total_amount = 0.0
        self.created_at = datetime.now()

    def mark_paid(self):
        if self.status != self.STATUS_PENDING:
            raise ValueError(f"Cannot pay order in status: {self.status}")
        self.status = self.STATUS_PAID

    def mark_shipped(self):
        if self.status != self.STATUS_PAID:
            raise ValueError(f"Cannot ship order in status: {self.status}")
        self.status = self.STATUS_SHIPPED

    def mark_cancelled(self):
        if self.status == self.STATUS_SHIPPED:
            raise ValueError("Cannot cancel a shipped order")
        self.status = self.STATUS_CANCELLED

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "items": self.items,
            "status": self.status,
            "total_amount": self.total_amount,
        }