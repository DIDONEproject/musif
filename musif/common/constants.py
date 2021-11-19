import logging
from enum import Enum

ENCODING = 'utf-8'
VERSION = "1.0.0"
CSV_DELIMITER = ","
VOICE_FAMILY = "voice"
GENERAL_FAMILY = "general"
FEATURES_MODULE = "musif.extract.features"


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#These are the sequences needed to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

LEVEL_DEBUG = logging.getLevelName(logging.DEBUG)
LEVEL_INFO = logging.getLevelName(logging.INFO)
LEVEL_WARNING = logging.getLevelName(logging.WARNING)
LEVEL_ERROR = logging.getLevelName(logging.ERROR)
LEVEL_CRITICAL = logging.getLevelName(logging.CRITICAL)


COLORS = {
    LEVEL_DEBUG: BLUE,
    LEVEL_INFO: WHITE,
    LEVEL_WARNING: YELLOW,
    LEVEL_ERROR: RED,
    LEVEL_CRITICAL: YELLOW,
}
