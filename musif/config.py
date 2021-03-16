import multiprocessing
from glob import glob
from os import path
from typing import List

from musif.common.logs import get_logger
from musif.common.utils import get_file_name, read_dicts_from_csv, read_object_from_json_file
from musif.features.feature import Features


READ_LOGGER_NAME = "read"
WRITE_LOGGER_NAME = "write"


class Configuration:
    def __init__(
        self,
        data_dir: str,
        metadata_dir: str,
        intermediate_files_dir: str,
        logs_dir: str,
        log_level: str,
        sequential: bool,
        features: List[str],
        split: bool,
    ):
        self.data_dir = data_dir
        self.metadata_dir = metadata_dir
        self.logs_dir = logs_dir
        self.scores_metadata = {
            get_file_name(file): read_dicts_from_csv(file) for file in glob(path.join(self.metadata_dir, "*.csv"))
        }
        self.characters_gender = read_dicts_from_csv(path.join(self.data_dir, "characters_gender.csv"))
        self.sound_to_abbreviation = read_object_from_json_file(path.join(self.data_dir, "sound_abbreviation.json"))
        self.abbreviation_to_sound = {abbreviation: sound for sound, abbreviation in self.sound_to_abbreviation.items()}
        self.sound_to_family = read_object_from_json_file(path.join(self.data_dir, "sound_family.json"))
        self.family_to_abbreviation = read_object_from_json_file(path.join(self.data_dir, "family_abbreviation.json"))
        self.translations_cache = read_object_from_json_file(path.join(self.data_dir, "translations.json"))
        self.scoring_order = read_object_from_json_file(path.join(self.data_dir, "scoring_order.json"))
        self.scoring_family_order = read_object_from_json_file(path.join(self.data_dir, "scoring_family_order.json"))
        self.read_logger = get_logger(READ_LOGGER_NAME, "read.log", self.logs_dir, log_level)
        self.write_logger = get_logger(WRITE_LOGGER_NAME, "write.log", self.logs_dir, log_level)
        self.cpu_workers = (
            multiprocessing.cpu_count() - 2 if multiprocessing.cpu_count() > 3 else multiprocessing.cpu_count() // 2
        )
        self.intermediate_files_dir = intermediate_files_dir
        self.sequential = sequential
        self.features = [Features(features_name) for features_name in features]
        self.split = split
