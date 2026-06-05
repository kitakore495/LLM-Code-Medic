from config.settings import (
    DEFAULT_TAX,
    DEFAULT_DISCOUNT
)


def calculate_tax(price):
    return price * DEFAULT_TAX


def calculate_discount(price):
    return price * DEFAULT_DISCOUNT


def calculate_total(price, tax, discount):
    return price + tax - discount


def calculate_shipping(price):
    if price > 1000:
        return 0
    return 20


def calculate_final_amount(price):
    tax = calculate_tax(price)
    discount = calculate_discount(price)
    return calculate_total(price, tax, discount)