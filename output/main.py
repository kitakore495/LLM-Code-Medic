from models.order import Order
from models.product import Product
from pipeline.order_pipeline import run_order_pipeline, run_report_pipeline
from repository.product_repository import save_product


def build_demo_data():
    p1 = Product("P001", "Wireless Headphones", price=89.99, stock=50)
    p2 = Product("P002", "USB-C Cable", price=12.99, stock=200)
    save_product(p1)
    save_product(p2)

    order = Order(
        order_id="ORD-2024-001",
        user_id="USR-001",
        items=[
            {"product_id": "P001", "quantity": 2, "unit_price": 89.99},
            {"product_id": "P002", "quantity": 3, "unit_price": 12.99},
        ],
    )
    return order


def run_pipeline():
    print("=== Warehouse Management System ===")
    order = build_demo_data()

    print(f"Processing order: {order.order_id}")
    result = run_order_pipeline(order)
    print(f"Order result: {result}")

    print(f"Generating report for user: {order.user_id}")
    report = run_report_pipeline(order.user_id)
    print(report)

    print("=== Pipeline Complete ===")


if __name__ == "__main__":
    run_pipeline()