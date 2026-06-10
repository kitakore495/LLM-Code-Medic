# BUG-5: 函数名拼写错误 format_curency（少一个r），report_service import 了 format_currency
from config.settings import DEFAULT_CURRENCY


def format_curency(amount: float, currency: str = DEFAULT_CURRENCY) -> str:
    # BUG-5: 函数名应为 format_currency
    return f"{currency} {amount:.2f}"


def format_order_summary(order) -> str:
    lines = [f"Order #{order.order_id}"]
    for item in order.items:
        lines.append(
            f"  - {item['product_id']} x{item['quantity']} "
            f"@ {format_curency(item['unit_price'])}"
        )
    lines.append(f"  Total: {format_curency(order.total_amount)}")
    lines.append(f"  Status: {order.status}")
    return "\n".join(lines)


def format_product_info(product) -> str:
    return (
        f"[{product.product_id}] {product.name} | "
        f"Price: {format_curency(product.price)} | "
        f"Stock: {product.stock}"
    )