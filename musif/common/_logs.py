import logging
import sys
from logging import Logger
from logging.handlers import TimedRotatingFileHandler
from os import mkdir, path

from musif.common.constants import (
    LEVEL_CRITICAL,
    LEVEL_DEBUG,
    LEVEL_ERROR,
    LEVEL_INFO,
    LEVEL_WARNING,
)
from musif.common._utils import colorize


class ConsoleFormatter(logging.Formatter):

    format = "%(message)s"

    FORMATS = {
        logging.DEBUG: colorize(format, LEVEL_DEBUG),
        logging.INFO: colorize(format, LEVEL_INFO),
        logging.WARNING: colorize(format, LEVEL_WARNING),
        logging.ERROR: colorize(format, LEVEL_ERROR),
        logging.CRITICAL: colorize(format, LEVEL_CRITICAL),
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class FileFormatter(logging.Formatter):

    FORMAT = "%(asctime)s %(levelname)s %(message)s"

    def format(self, record):
        formatter = logging.Formatter(self.FORMAT)
        return formatter.format(record)


def set_logger_file_handler(
    logger: Logger, log_file_path: str = None, file_log_level: str = None
):
    if log_file_path is None or file_log_level is None:
        return
    log_filename = path.basename(log_file_path)
    log_dir = log_file_path[: -len(log_filename)]
    if not path.exists(log_dir):
        mkdir(log_dir)
    file_handler = TimedRotatingFileHandler(
        log_file_path, when="midnight", backupCount=5
    )
    file_handler.setLevel(file_log_level)
    file_handler.setFormatter(FileFormatter())
    logger.addHandler(file_handler)


def set_logger_console_handler(logger: Logger, console_log_level: str = None):
    if console_log_level is None:
        return
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(ConsoleFormatter())
    logger.addHandler(console_handler)


def create_logger(
    logger_name: str,
    log_file_path: str = None,
    file_log_level: str = None,
    console_log_level: str = None,
) -> Logger:
    logger = logging.getLogger()
    logger.setLevel(LEVEL_DEBUG)
    logger.propagate = False
    for handler in logger.handlers:
        logger.removeHandler(handler)
    set_logger_file_handler(logger, log_file_path, file_log_level)
    set_logger_console_handler(logger, console_log_level)
