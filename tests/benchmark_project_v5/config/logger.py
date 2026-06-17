import logging
from datetime import datetime

LOG_LEVEL = logging.INFO


class AppLogger:
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(LOG_LEVEL)

    def info(self, msg: str):
        self._logger.info(f"[{datetime.now().isoformat()}] INFO  | {msg}")

    def warning(self, msg: str):
        self._logger.warning(f"[{datetime.now().isoformat()}] WARN  | {msg}")

    def error(self, msg: str):
        self._logger.error(f"[{datetime.now().isoformat()}] ERROR | {msg}")

    def debug(self, msg: str):
        self._logger.debug(f"[{datetime.now().isoformat()}] DEBUG | {msg}")


logger = AppLogger("warehouse")