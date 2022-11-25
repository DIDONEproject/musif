import logging

"""
Common constants to be used transversaly throught modules
"""

"""Sequences needed to get colored ouput and reset back to normal"""
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


"""Logging constants to introduce in the logger"""
LEVEL_DEBUG = logging.getLevelName(logging.DEBUG)
LEVEL_INFO = logging.getLevelName(logging.INFO)
LEVEL_WARNING = logging.getLevelName(logging.WARNING)
LEVEL_ERROR = logging.getLevelName(logging.ERROR)
LEVEL_CRITICAL = logging.getLevelName(logging.CRITICAL)

"""Indexes for each color"""
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

"""Dictionary to access different color indexes for logging"""
COLORS = {
    LEVEL_DEBUG: BLUE,
    LEVEL_INFO: WHITE,
    LEVEL_WARNING: YELLOW,
    LEVEL_ERROR: RED,
    LEVEL_CRITICAL: YELLOW,
}
