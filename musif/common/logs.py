import logging
import sys
from logging import Logger
from logging.handlers import TimedRotatingFileHandler
from os import mkdir, path

from musif.common.constants import LEVEL_CRITICAL, LEVEL_DEBUG, LEVEL_ERROR, LEVEL_INFO, LEVEL_WARNING
from musif.common.utils import colorize


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


def get_logger(logger_name: str, log_file_path: str, file_log_level: str, console_log_level: str) -> Logger:
    logger = logging.getLogger(logger_name)

    if logger.hasHandlers():
        return logger

    if log_file_path and file_log_level:
        logger.propagate = False
        logger.setLevel(LEVEL_DEBUG)
        log_filename = path.basename(log_file_path)
        log_dir = log_file_path[:-len(log_filename)]
        if not path.exists(log_dir):
            mkdir(log_dir)
        log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        file_handler = TimedRotatingFileHandler(log_file_path, when="midnight", backupCount=5)
        file_handler.setLevel(file_log_level)
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)

    if console_log_level:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_log_level)
        console_handler.setFormatter(ConsoleFormatter())
        logger.addHandler(console_handler)

    return logger
