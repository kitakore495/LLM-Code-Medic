def format_currency(amount):
    return f"${amount:.2f}"


def format_order(order):
    return (
        f"Order("
        f"user={order.user_id}, "
        f"product={order.product}, "
        f"amount={order.amount})"
    )


def format_user(user):
    return f"{user['name']} <{user['email']}>"


# --------------------------------
# Hidden Bug (拼写错误，用于静态分析测试)
# --------------------------------

def format_curreny(amount):
    return f"${amount}"