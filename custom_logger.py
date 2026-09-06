"""Console and file logging."""
import logging
import os


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        return super().format(record)


class CustomLogger:
    def __init__(self):
        os.makedirs("log", exist_ok=True)
        self.logger = logging.getLogger("Stockagent")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            file_handler = logging.FileHandler("log/simulation.log", encoding="utf-8")
            file_handler.setFormatter(logging.Formatter(fmt))
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(ColoredFormatter(fmt))
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)


log = CustomLogger()
