import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from os import mkdir, path


def get_logger(logger_name: str, log_file_name: str, logs_dir: str = None, log_level: str = None):
    logger = logging.getLogger(logger_name)
    if not logger.hasHandlers():
        logger.propagate = False
        logger.setLevel(logging.getLevelName(logging.DEBUG))
        if not path.exists(logs_dir):
            mkdir(logs_dir)
        log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        file_handler = TimedRotatingFileHandler(path.join(logs_dir, log_file_name), when="midnight", backupCount=5)
        file_handler.setLevel(logging.getLevelName(logging.DEBUG))
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)
        log_formatter = logging.Formatter("%(levelname)s %(message)s")
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.getLevelName(logging.INFO))
        logger.addHandler(console_handler)
    return logger
