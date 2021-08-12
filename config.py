import multiprocessing
from glob import glob
from os import path

from musif.common.logs import get_logger
from musif.common.utils import read_dicts_from_csv, read_object_from_json_file, read_object_from_yaml_file
from musif.extract.model import Level

READ_LOGGER_NAME = "read"
READ_LOG_FILE_NAME = "read.log"
WRITE_LOGGER_NAME = "write"
WRITE_LOG_FILE_NAME = "write.log"

_CONFIG_FALLBACK = {
    "logs_dir": "logs",
    "log_level": "DEBUG",
    "data_dir": "data",
    "metadata_dir": "metadata",
    "metadata_id_col": "FileName",
    "intermediate_dir": "intermediate",
    "parallel": False,
    "max_processes": 1,
    "features": None,
    "split_keywords": [],
    "level": Level.SCORE.value,
}

class Configuration:

    def __init__(self, *args, **kwargs):
        config_data = {}
        if len(args) > 0:
            if isinstance(args[0], str):
                config_data = read_object_from_yaml_file(args[0])
            elif isinstance(args[0], dict):
                config_data = args[0]
        config_data.update(kwargs)
        self.logs_dir = config_data.get("logs_dir", _CONFIG_FALLBACK["logs_dir"])
        self.log_level = config_data.get("log_level", _CONFIG_FALLBACK["log_level"])
        self.data_dir = config_data.get("data_dir", _CONFIG_FALLBACK["data_dir"])
        self.metadata_dir = config_data.get("metadata_dir", _CONFIG_FALLBACK["metadata_dir"])
        self.metadata_id_col = config_data.get("metadata_id_col", _CONFIG_FALLBACK["metadata_id_col"])
        self.intermediate_dir = config_data.get("intermediate_files_dir", _CONFIG_FALLBACK["intermediate_dir"])
        self.parallel = config_data.get("parallel", _CONFIG_FALLBACK["parallel"])
        self.max_processes = config_data.get("max_processes", _CONFIG_FALLBACK["max_processes"])
        self.features = config_data.get("features", _CONFIG_FALLBACK["features"])
        self.split_keywords = config_data.get("split_keywords", _CONFIG_FALLBACK["split_keywords"])
        self.level = Level(config_data.get("level", _CONFIG_FALLBACK["level"]))
        self.scores_metadata = {
            path.basename(file): read_dicts_from_csv(file) for file in glob(path.join(self.metadata_dir, "score", "*.csv"))
        }
        self.characters_gender = read_dicts_from_csv(path.join(self.data_dir, "characters_gender.csv"))
        self.sound_to_abbreviation = read_object_from_json_file(path.join(self.data_dir, "sound_abbreviation.json"))
        self.abbreviation_to_sound = {abbreviation: sound for sound, abbreviation in self.sound_to_abbreviation.items()}
        self.sound_to_family = read_object_from_json_file(path.join(self.data_dir, "sound_family.json"))
        self.family_to_abbreviation = read_object_from_json_file(path.join(self.data_dir, "family_abbreviation.json"))
        self.translations_cache = read_object_from_json_file(path.join(self.data_dir, "translations.json"))
        self.scoring_order = read_object_from_json_file(path.join(self.data_dir, "scoring_order.json"))
        self.scoring_family_order = read_object_from_json_file(path.join(self.data_dir, "scoring_family_order.json"))
        self.sorting_lists = read_object_from_json_file(path.join(self.data_dir, "sorting_lists.json"))
        self.cpu_workers = (
            multiprocessing.cpu_count() - 2 if multiprocessing.cpu_count() > 3 else multiprocessing.cpu_count() // 2
        )

    def is_required_module(self, module) -> bool:
        if self.features is None:
            return True
        module_name = module.__name__
        features = {feature.lower() for feature in self.features}
        module_feature = module_name[module_name.rindex(".") + 1:].lower()
        return module_feature in features


config = Configuration("config.yml")
read_logger = get_logger(READ_LOGGER_NAME, READ_LOG_FILE_NAME, config.logs_dir, config.log_level)
write_logger = get_logger(WRITE_LOGGER_NAME, WRITE_LOG_FILE_NAME, config.logs_dir, config.log_level)
