import logging
from logging import Logger, getLogger

from musif.common.constants import (
    LEVEL_CRITICAL,
    LEVEL_DEBUG,
    LEVEL_ERROR,
    LEVEL_INFO,
    LEVEL_WARNING,
)
from musif.common._utils import colorize
from musif.config import LOGGER_NAME

"""
This module contains functions that display information when using musif. 
Functionts starting with 'l' are using for logging, while function starting by
'p' are used for terminal display. The messages will be out puted acoording to the level set
in the configuration file.
"""


def linfo(text: str, exc_info: bool = False) -> None:
    llog(text, logger(), LEVEL_INFO, exc_info)


def ldebug(text: str, exc_info: bool = False) -> None:
    llog(text, logger(), LEVEL_DEBUG, exc_info)


def lwarn(text: str, exc_info: bool = False) -> None:
    llog(text, logger(), LEVEL_WARNING, exc_info)


def lerr(text: str, exc_info: bool = False) -> None:
    llog(text, logger(), LEVEL_ERROR, exc_info)


def lcrit(text: str, exc_info: bool = False) -> None:
    llog(text, logger(), LEVEL_CRITICAL, exc_info)


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
