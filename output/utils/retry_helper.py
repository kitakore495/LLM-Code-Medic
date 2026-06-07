# 修复：MAX_RETRY_COUNT → MAX_RETRIES
import time
from config.settings import MAX_RETRIES


def retry(func, *args, **kwargs):
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            time.sleep(0.1)
    raise RuntimeError(
        f"Function {func.__name__} failed after {MAX_RETRIES} retries"
    ) from last_exc


def with_timeout(func, timeout_seconds: float, *args, **kwargs):
    import threading
    result = [None]
    exc = [None]

    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exc[0] = e

    t = threading.Thread(target=target)
    t.start()
    t.join(timeout=timeout_seconds)
    if t.is_alive():
        raise TimeoutError(f"{func.__name__} timed out after {timeout_seconds}s")
    if exc[0]:
        raise exc[0]
    return result[0]