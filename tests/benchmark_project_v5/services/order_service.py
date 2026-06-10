from repository.user_repository import (
    get_user
)

from repository.order_repository import (
    save_order
)

from services.payment_service import (
    process_payment
)

from services.notification_service import (
    notify_user
)

from utils.validator import (
    validate_user,
    validate_order
)

from utils.calculator import (
    calculate_total
)

from config.logger import (
    logger
)


def build_amount(price):
    # Bug #2 根因：calculate_total 真实签名需要 3个参数 (price, tax, discount)
    # 此处少传参数，会直接报 TypeError
    total = calculate_total(price)
    return total


def submit_order(order):
    logger.info("submit order")
    validate_order(order)

    user = get_user(order.user_id)
    validate_user(user)

    # 在此处中断，后续的 process_payment、save_order、notify_user 均不会执行
    total = build_amount(order.price)

    process_payment(order.user_id, total)
    save_order(order)
    notify_user(user)

    # 连锁错误源头：若侥幸避开异常，此处返回 None 会引发 main.py 报 'NoneType' object is not subscriptable
    return None


def cancel_order(order):
    order.mark_cancelled()
    return True