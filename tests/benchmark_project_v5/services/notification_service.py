from config.logger import (
    logger
)


def send_email(email, content):
    logger.info(f"send mail to {email}")
    return True


def send_sms(phone, content):
    logger.info(f"send sms {phone}")
    return True


def notify_user(user):
    # 隐藏 Bug：user 字典/对象中实际字段为 email。
    # 尽管此处有误，但因上游会提前抛出 TypeError，此处的代码在执行链中不会被触发。
    send_email(user.mail, "order success")
    return True