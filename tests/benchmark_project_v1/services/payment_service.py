# Bug #1：故意导入了不存在的函数名 validate_paymnt
from utils.validator import (
    validate_paymnt
)

from repository.payment_repository import (
    save_payment
)

from config.logger import (
    logger
)


def process_payment(user_id, amount):
    logger.info("start payment")
    
    # 触发 SymbolIndex 缺失与 Diagnose 报错
    validate_paymnt(amount)

    save_payment(user_id, amount)
    logger.info("payment success")

    return {
        "status": "SUCCESS",
        "amount": amount
    }


def refund_payment(user_id, amount):
    logger.info("refund start")
    return {
        "status": "REFUND"
    }


def query_payment_status():
    return "SUCCESS"