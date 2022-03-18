from os import path
 
BASE_PATH = path.join("tests", "data")
DATA_STATIC_DIR = path.join(BASE_PATH, "static")

INCOMPLETE_FILE = path.join(BASE_PATH, "arias_test", "others", "incomplete.xml")
MALFORMED_FILE = path.join(BASE_PATH, "arias_test", "others", "malformed.xml")
CONFIG_PATH=path.join(BASE_PATH, "config_test")
CONFIG_FILE = path.join(CONFIG_PATH, "config.yml")
          
TEST_FILE = "Did03M-Son_regina-1730-Sarro[1.05][0006].xml"