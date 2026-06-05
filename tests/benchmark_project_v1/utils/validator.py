def validate_user(user):
    if user is None:
        raise ValueError("user not found")
    return True


def validate_order(order):
    if order is None:
        raise ValueError("order is none")
    if order.price <= 0:
        raise ValueError("invalid price")
    return True


def validate_payment(amount):
    if amount <= 0:
        raise ValueError("invalid payment")
    return True


def validate_address(address):
    if not address:
        raise ValueError("empty address")
    return True


def validate_email(email):
    if "@" not in email:
        raise ValueError("invalid email")
    return True