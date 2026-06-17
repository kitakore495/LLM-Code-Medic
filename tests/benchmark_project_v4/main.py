from services.order_service import submit_order
from models.order import Order


def build_demo_order():
    return Order(
        user_id=1001,
        product="Laptop",
        price=5000
    )


def run_pipeline():

    order = build_demo_order()

    result = submit_order(order)

    print("订单状态：")

    print(result["status"])


if __name__ == "__main__":
    run_pipeline()