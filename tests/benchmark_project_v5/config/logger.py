import datetime


class Logger:

    def info(self, msg):

        print(
            f"[INFO]"
            f"[{datetime.datetime.now()}]"
            f" {msg}"
        )

    def warning(self, msg):

        print(
            f"[WARN]"
            f"[{datetime.datetime.now()}]"
            f" {msg}"
        )

    def error(self, msg):

        print(
            f"[ERROR]"
            f"[{datetime.datetime.now()}]"
            f" {msg}"
        )


logger = Logger()