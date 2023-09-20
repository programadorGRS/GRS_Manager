from logging import (DEBUG, ERROR, FileHandler, Filter, Formatter, LogRecord,
                     StreamHandler)

from flask import Flask
from flask.logging import default_handler


class LessThanErrorFilter(Filter):
    def __init__(self, name: str = "") -> None:
        """Aceita apenas logs menores do que ERROR"""
        super().__init__(name)
        self.error_lvl = ERROR

    def filter(self, record: LogRecord):
        if record.levelno < self.error_lvl:
            return True
        else:
            return False


def setup_loggers(app: Flask):
    default_fmt = Formatter(
        fmt="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )

    # accept only logs below ERROR level
    std_file_handler = FileHandler(filename=app.config.get("STD_LOG_FILE"))  # type: ignore
    std_file_handler.set_name("std_log")
    std_file_handler.setFormatter(fmt=default_fmt)
    std_file_handler.setLevel(DEBUG)
    std_filter = LessThanErrorFilter()
    std_file_handler.addFilter(std_filter)

    # accept only logs equal or above ERROR level
    err_file_handler = FileHandler(filename=app.config.get("ERR_LOG_FILE"))  # type: ignore
    err_file_handler.set_name("err_log")
    err_file_handler.setFormatter(fmt=default_fmt)
    err_file_handler.setLevel(ERROR)

    # accept all logs
    console_handler = StreamHandler()
    console_handler.set_name("debug_log")
    console_handler.setFormatter(default_fmt)
    console_handler.setLevel(DEBUG)

    app.logger.addHandler(std_file_handler)
    app.logger.addHandler(err_file_handler)
    app.logger.addHandler(console_handler)

    app.logger.removeHandler(default_handler)

    return app
