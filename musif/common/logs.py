import logging
from logging.handlers import TimedRotatingFileHandler
from os import mkdir, path


def get_logger(logger_name: str, log_file_path: str, log_level: str = None) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    if not logger.hasHandlers():
        logger.propagate = False
        logger.setLevel(log_level)
        log_filename = path.basename(log_file_path)
        log_dir = log_file_path[:-len(log_filename)]
        if not path.exists(log_dir):
            mkdir(log_dir)
        log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        file_handler = TimedRotatingFileHandler(log_file_path, when="midnight", backupCount=5)
        file_handler.setLevel(logging.getLevelName(logging.DEBUG))
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)
    return logger
