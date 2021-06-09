import multiprocessing
from glob import glob
from os import path

from musif.common.logs import get_logger
from musif.common.utils import read_dicts_from_csv, read_object_from_json_file, read_object_from_yaml_file
from musif.extract.model import Features, Level

READ_LOGGER_NAME = "read"
WRITE_LOGGER_NAME = "write"


_CONFIG_FALLBACK = {
    "data_dir": "data",
    "metadata_dir": "metadata",
    "metadata_id_col": "FileName",
    "intermediate_dir": "intermediate",
    "logs_dir": "logs",
    "log_level": "DEBUG",
    "parallel": False,
    "max_processes": 1,
    "features": [features.value for features in Features],
    "split_keywords": [],
    "level": Level.SCORE.value,
    "merge_voices": False,
    "require_harmonic_analysis": False
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
        self.data_dir = config_data.get("data_dir", _CONFIG_FALLBACK["data_dir"])
        self.metadata_dir = config_data.get("metadata_dir", _CONFIG_FALLBACK["metadata_dir"])
        self.metadata_id_col = config_data.get("metadata_id_col", _CONFIG_FALLBACK["metadata_id_col"])
        self.logs_dir = config_data.get("logs_dir", _CONFIG_FALLBACK["logs_dir"])
        log_level = config_data.get("log_level", _CONFIG_FALLBACK["log_level"])
        self.intermediate_dir = config_data.get("intermediate_files_dir", _CONFIG_FALLBACK["intermediate_dir"])
        self.parallel = config_data.get("parallel", _CONFIG_FALLBACK["parallel"])
        self.max_processes = config_data.get("max_processes", _CONFIG_FALLBACK["max_processes"])
        features = config_data.get("features", _CONFIG_FALLBACK["features"])
        self.features = [Features(features_name) for features_name in features]
        self.split_keywords = config_data.get("split_keywords", _CONFIG_FALLBACK["split_keywords"])
        self.level = Level(config_data.get("level", _CONFIG_FALLBACK["level"]))
        self.merge_voices = config_data.get("merge_voices", _CONFIG_FALLBACK["merge_voices"])
        self.require_harmonic_analysis = config_data.get("require_harmonic_analysis", _CONFIG_FALLBACK["require_harmonic_analysis"])

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
        self.read_logger = get_logger(READ_LOGGER_NAME, "read.log", self.logs_dir, log_level)
        self.write_logger = get_logger(WRITE_LOGGER_NAME, "write.log", self.logs_dir, log_level)
        self.cpu_workers = (
            multiprocessing.cpu_count() - 2 if multiprocessing.cpu_count() > 3 else multiprocessing.cpu_count() // 2
        )
