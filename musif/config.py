import multiprocessing
from glob import glob
from os import path

from musif.common.logs import get_logger
from musif.common.utils import read_dicts_from_csv, read_object_from_json_file, read_object_from_yaml_file

from musif import internal_data

READ_LOGGER_NAME = "read_log"
WRITE_LOGGER_NAME = "write_log"

READ_LOG = "read_log"
WRITE_LOG = "write_log"
LOG_FILE_PATH = "file_path"
FILE_LOG_LEVEL = "file_level"
CONSOLE_LOG_LEVEL = "console_level"
METADATA_DIR = "metadata_dir"
METADATA_ID_COL = "metadata_id_col"
DATA_DIR = "data_dir"
MUSESCORE_DIR = "musescore_dir"
PARALLEL = "parallel"
MAX_PROCESSES = "max_processes"
FEATURES = "features"
SPLIT_KEYWORDS = "split_keywords"
PARTS_FILTER = "parts_filter"
EXPAND_REPEATS = "expand_repeats"

_CONFIG_FALLBACK = {
    READ_LOG: {
        LOG_FILE_PATH: "logs/read.log",
        FILE_LOG_LEVEL: "DEBUG",
        CONSOLE_LOG_LEVEL: "INFO",
    },
    WRITE_LOG: {
        LOG_FILE_PATH: "logs/write.log",
        FILE_LOG_LEVEL: "ERROR",
        CONSOLE_LOG_LEVEL: "INFO",
    },
    METADATA_DIR: "metadata",
    METADATA_ID_COL: "FileName",
    DATA_DIR: ".",
    MUSESCORE_DIR: None,
    PARALLEL: False,
    MAX_PROCESSES: 1,
    FEATURES: None,
    SPLIT_KEYWORDS: [],
    PARTS_FILTER: [],
    EXPAND_REPEATS: False,
}


class Configuration:

    def __init__(self, *args, **kwargs):
        config_data = {}
        if len(args) > 1:
            raise ValueError(f"Unexpected number of args passed to constructor: {len(args)}")
        if len(args) > 0:
            if isinstance(args[0], str):
                config_data = read_object_from_yaml_file(args[0])
            elif isinstance(args[0], dict):
                config_data = args[0]
            elif isinstance(args[0], Configuration):
                config_data = args[0].to_dict()
            else:
                raise TypeError()
        config_data.update(kwargs)  # Override values
        read_log_config = config_data.get(READ_LOG, _CONFIG_FALLBACK[READ_LOG])
        self.read_log_file = read_log_config[LOG_FILE_PATH]
        self.read_file_log_level = read_log_config[FILE_LOG_LEVEL]
        self.read_console_log_level = read_log_config[CONSOLE_LOG_LEVEL]
        self.read_logger = get_logger(READ_LOGGER_NAME, self.read_log_file, self.read_file_log_level, self.read_console_log_level)
        write_log_config = config_data.get(WRITE_LOG, _CONFIG_FALLBACK[WRITE_LOG])
        self.write_log_file = write_log_config[LOG_FILE_PATH]
        self.write_file_log_level = write_log_config[FILE_LOG_LEVEL]
        self.write_console_log_level = write_log_config[CONSOLE_LOG_LEVEL]
        self.write_logger = get_logger(READ_LOGGER_NAME, self.write_log_file, self.write_file_log_level, self.write_console_log_level)
        self.metadata_dir = config_data.get(METADATA_DIR, _CONFIG_FALLBACK[METADATA_DIR])
        self.metadata_id_col = config_data.get(METADATA_ID_COL, _CONFIG_FALLBACK[METADATA_ID_COL])
        self.data_dir = config_data.get(DATA_DIR, _CONFIG_FALLBACK[DATA_DIR])
        self.musescore_dir = config_data.get(MUSESCORE_DIR, _CONFIG_FALLBACK[MUSESCORE_DIR])
        self.parallel = config_data.get(PARALLEL, _CONFIG_FALLBACK[PARALLEL])
        self.max_processes = config_data.get(MAX_PROCESSES, _CONFIG_FALLBACK[MAX_PROCESSES])
        self.features = config_data.get(FEATURES, _CONFIG_FALLBACK[FEATURES])
        self.split_keywords = config_data.get(SPLIT_KEYWORDS, _CONFIG_FALLBACK[SPLIT_KEYWORDS])
        self.parts_filter = config_data.get(PARTS_FILTER, _CONFIG_FALLBACK[PARTS_FILTER])
        self.expand_repeats = config_data.get(EXPAND_REPEATS, _CONFIG_FALLBACK[EXPAND_REPEATS])
        self.internal_data_dir = path.dirname(internal_data.__file__)
        self._load_metadata()

    def is_requested_feature_category(self, feature) -> bool:
        if self.features is None:
            return True
        return feature in self.features

    def is_requested_module(self, module) -> bool:
        if self.features is None:
            return True
        module_path = module.__name__
        module_name = module_path if "." not in module_path else module_path[module_path.rindex(".") + 1:]
        for feature in self.features:
            if feature.lower().endswith(module_name.lower()):
                return True
        return False

    def to_dict(self) -> dict:
        return {
            READ_LOG: {
                LOG_FILE_PATH: self.read_log_file,
                FILE_LOG_LEVEL: self.read_file_log_level,
                CONSOLE_LOG_LEVEL: self.read_console_log_level,
            },
            WRITE_LOG: {
                LOG_FILE_PATH: self.write_log_file,
                FILE_LOG_LEVEL: self.write_file_log_level,
                CONSOLE_LOG_LEVEL: self.write_console_log_level,
            },
            METADATA_DIR: self.metadata_dir,
            METADATA_ID_COL: self.metadata_id_col,
            DATA_DIR: self.data_dir,
            MUSESCORE_DIR: self.musescore_dir,
            PARALLEL: self.parallel,
            MAX_PROCESSES: self.max_processes,
            FEATURES: self.features,
            SPLIT_KEYWORDS: list(self.split_keywords),
            PARTS_FILTER: list(self.parts_filter),
            EXPAND_REPEATS: self.expand_repeats,
        }

    def _load_metadata(self) -> None:
        self.scores_metadata = {
            path.basename(file): read_dicts_from_csv(file) for file in
            glob(path.join(self.metadata_dir, "score", "*.csv"))
        }
        self.characters_gender = read_dicts_from_csv(path.join(self.internal_data_dir, "characters_gender.csv"))
        self.sound_to_abbreviation = read_object_from_json_file(path.join(self.internal_data_dir, "sound_abbreviation.json"))
        self.abbreviation_to_sound = {abbreviation: sound for sound, abbreviation in self.sound_to_abbreviation.items()}
        self.sound_to_family = read_object_from_json_file(path.join(self.internal_data_dir, "sound_family.json"))
        self.family_to_abbreviation = read_object_from_json_file(path.join(self.internal_data_dir, "family_abbreviation.json"))
        self.translations_cache = read_object_from_json_file(path.join(self.internal_data_dir, "translations.json"))
        self.scoring_order = read_object_from_json_file(path.join(self.internal_data_dir, "scoring_order.json"))
        self.scoring_family_order = read_object_from_json_file(path.join(self.internal_data_dir, "scoring_family_order.json"))
        self.sorting_lists = read_object_from_json_file(path.join(self.internal_data_dir, "sorting_lists.json"))
        self.cpu_workers = (
            multiprocessing.cpu_count() - 2 if multiprocessing.cpu_count() > 3 else multiprocessing.cpu_count() // 2
        )
