import logging
from logging import Logger, getLogger
from tkinter.messagebox import NO

from musif.common.constants import LEVEL_CRITICAL, LEVEL_DEBUG, LEVEL_ERROR, LEVEL_INFO, \
    LEVEL_WARNING
from musif.common.utils import colorize
from musif.config import LOGGER_NAME

# manager = multiprocessing.Manager()
# logger_list=manager.list()


# class Mymanager (BaseManager):
#     pass

def createlogger(log_path, console_level= None,file_level= None):
        logger=logging.getLogger()
        formatting='%(asctime)s %(levelname)-8s %(message)s'
        
        if console_level is None:
            console_level = logger.level
        ch = logging.StreamHandler()
        ch.setLevel(level=console_level)
        ch.setFormatter(logging.Formatter(formatting))
        logger.addHandler(ch)

        if file_level is None:
            file_level = logger.level
        fh = logging.FileHandler(log_path)
        fh.setLevel(level=file_level)
        fh.setFormatter(logging.Formatter(formatting))
        logger.addHandler(fh)
        return logger

        
# Mymanager.register('mylogger', mylogger)

# manager = Mymanager()
# logger = manager.mylogger()

def linfo(text: str, logger, exc_info: bool = False) -> None:
    llog(text, logger, LEVEL_INFO, exc_info)


def ldebug(text: str, exc_info: bool = False) -> None:
    llog(text, LEVEL_DEBUG, exc_info)


def lwarn(text: str, exc_info: bool = False) -> None:
    llog(text, logger_list[0], LEVEL_WARNING, exc_info)


def lerr(text: str, exc_info: bool = False) -> None:
    llog(text, logger_list[0], LEVEL_ERROR, exc_info)


def lcrit(text: str, exc_info: bool = False) -> None:
    llog(text, logger_list[0], LEVEL_CRITICAL, exc_info)


def pinfo(text: str, level: str = LEVEL_INFO) -> None:
    plog(text, LEVEL_INFO, allowed_level=level)


def pdebug(text: str, level: str = LEVEL_INFO) -> None:
    plog(text, LEVEL_DEBUG, allowed_level=level)


def pwarn(text: str, level: str = LEVEL_INFO) -> None:
    plog(text, LEVEL_WARNING, allowed_level=level)


def perr(text: str, level: str = LEVEL_INFO) -> None:
    plog(text, LEVEL_ERROR, allowed_level=level)


def pcrit(text: str, level: str = LEVEL_INFO) -> None:
    plog(text, LEVEL_CRITICAL, allowed_level=level)


def logger() -> Logger:
    return getLogger(LOGGER_NAME)


def llog(text: str, logger: logging.Logger, level: str, exc_info: bool) -> None:
    logger.log(logging.getLevelName(level), text, exc_info=exc_info)


def plog(text: str, level: str, allowed_level: str = LEVEL_INFO) -> None:
    if logging.getLevelName(level) < logging.getLevelName(allowed_level):
        return
    print(colorize(text, level))
