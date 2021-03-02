import multiprocessing
from os import path

from musif.common.logs import get_logger
from musif.common.utils import read_object_from_json_file, read_object_from_yaml_file, read_dicts_from_csv

_DIR = path.split(__file__)[0]
_config = read_object_from_yaml_file(path.join(_DIR, "../config.yml"))

data_dir = _config["data_dir"]
logs_dir = _config["logs_dir"]

arias_metadata = read_dicts_from_csv(path.join(data_dir, "arias_metadata.csv"))
characters_gender = read_dicts_from_csv(path.join(data_dir, "characters_gender.csv"))
# arias_clefs = read_dicts_from_csv(path.join(data_dir, "arias_clefs.csv"))
sound_to_abbreviation = read_object_from_json_file(path.join(data_dir, "sound_abbreviation.json"))
abbreviation_to_sound = {abbreviation: sound for sound, abbreviation in sound_to_abbreviation.items()}
sound_to_family = read_object_from_json_file(path.join(data_dir, "sound_family.json"))
family_to_abbreviation = read_object_from_json_file(path.join(data_dir, "family_abbreviation.json"))
translations_cache = read_object_from_json_file(path.join(data_dir, "translations.json"))
scoring_order = read_object_from_json_file(path.join(data_dir, "scoring_order.json"))
scoring_family_order = read_object_from_json_file(path.join(data_dir, "scoring_family_order.json"))
read_logger = get_logger("read", "read.log", logs_dir, _config["log_level"])
write_logger = get_logger("write", "write.log", logs_dir, _config["log_level"])
cpu_workers = multiprocessing.cpu_count() - 2 if multiprocessing.cpu_count() > 3 else multiprocessing.cpu_count() // 2
default_intermediate_files_dir = _config["intermediate_files_dir"]
default_sequential = _config["sequential"]
default_features = _config["features"]
default_split = _config["split"]
