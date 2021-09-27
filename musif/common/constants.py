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

COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': YELLOW,
    'ERROR': RED
}

def get_color(levelname):
    return COLOR_SEQ % (30 + COLORS[levelname])