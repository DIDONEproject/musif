from enum import Enum

ENCODING = 'utf-8'
VERSION = "1.0.0"
CSV_DELIMITER = ","
VOICE_FAMILY = "voice"
GENERAL_FAMILY = "general"
FEATURES_MODULE = "musif.extract.features"


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


class Color(Enum):
    WARNING = YELLOW
    INFO = WHITE
    DEBUG = BLUE
    CRITICAL = YELLOW
    ERROR = RED
