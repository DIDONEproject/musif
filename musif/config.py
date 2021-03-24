import multiprocessing
from glob import glob
from os import path
from typing import List

from musif.common.logs import get_logger
from musif.common.utils import read_dicts_from_csv, read_object_from_json_file
from musif.extract.model import Features

READ_LOGGER_NAME = "read"
WRITE_LOGGER_NAME = "write"

_CONFIG_FALLBACK = {
    "data_dir": "data",
    "metadata_dir": "metadata",
    "metadata_id_col": "FileName",
    "intermediate_dir": "intermediate",
    "logs_dir": "logs",
    "log_level": "DEBUG",
    "sequential": True,
    "features": [features.value for features in Features],
    "split": True,
}

class Configuration:
    def __init__(
        self,
        data_dir: str = None,
        metadata_dir: str = None,
        metadata_id_col: str = None,
        intermediate_files_dir: str = None,
        logs_dir: str = None,
        log_level: str = None,
        sequential: bool = None,
        features: List[str] = None,
        split: bool = None,
    ):
        self.data_dir = data_dir or _CONFIG_FALLBACK["data_dir"]
        self.metadata_dir = metadata_dir or _CONFIG_FALLBACK["metadata_dir"]
        self.metadata_id_col = metadata_id_col or _CONFIG_FALLBACK["metadata_id_col"]
        self.logs_dir = logs_dir or _CONFIG_FALLBACK["logs_dir"]
        log_level = log_level or _CONFIG_FALLBACK["log_level"]
        self.intermediate_dir = intermediate_files_dir or _CONFIG_FALLBACK["intermediate_dir"]
        self.sequential = sequential or _CONFIG_FALLBACK["sequential"]
        features = features or _CONFIG_FALLBACK["features"]
        self.features = [Features(features_name) for features_name in features]
        self.split = split or _CONFIG_FALLBACK["split"]

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
