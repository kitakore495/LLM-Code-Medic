# 修复：函数名拼写错误 format_curency → format_currency；内部调用同步修正
from config.settings import DEFAULT_CURRENCY


def format_currency(amount: float, currency: str = DEFAULT_CURRENCY) -> str:
    return f"{currency} {amount:.2f}"


def format_order_summary(order) -> str:
    lines = [f"Order #{order.order_id}"]
    for item in order.items:
        lines.append(
            f"  - {item['product_id']} x{item['quantity']} "
            f"@ {format_currency(item['unit_price'])}"
        )
    lines.append(f"  Total: {format_currency(order.total_amount)}")
    lines.append(f"  Status: {order.status}")
    return "\n".join(lines)


def format_product_info(product) -> str:
    return (
        f"[{product.product_id}] {product.name} | "
        f"Price: {format_currency(product.price)} | "
        f"Stock: {product.stock}"
    )