import multiprocessing
from glob import glob
from os import path

from musif import internal_data
from musif.common.logs import create_logger
from musif.common.utils import read_dicts_from_csv, read_object_from_json_file, read_object_from_yaml_file
from musif.extract.constants import HARMONY_FEATURES, SCALE_RELATIVE_FEATURES

LOGGER_NAME = "musiF"
LOG = "log"
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
    LOG: {
        LOG_FILE_PATH: "./musiF.log",
        FILE_LOG_LEVEL: "DEBUG",
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
                raise TypeError(f"The argument type is {type(args[0])}, and it was expected a dictionary, a Configuration or a string object")
        config_data.update(kwargs)  # Override values
        log_config = config_data.get(LOG, _CONFIG_FALLBACK[LOG])
        self.log_file = log_config.get(LOG_FILE_PATH, _CONFIG_FALLBACK.get(LOG_FILE_PATH))
        self.file_log_level = log_config.get(FILE_LOG_LEVEL, _CONFIG_FALLBACK.get(FILE_LOG_LEVEL))
        self.console_log_level = log_config.get(CONSOLE_LOG_LEVEL, _CONFIG_FALLBACK.get(CONSOLE_LOG_LEVEL))
        create_logger(LOGGER_NAME, self.log_file, self.file_log_level, self.console_log_level)
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

    def is_requested_musescore_file(self) -> bool:
        if self.is_requested_feature_category(HARMONY_FEATURES):
            return True
        if self.is_requested_feature_category(SCALE_RELATIVE_FEATURES):
            return True
        return False

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
            LOG: {
                LOG_FILE_PATH: self.log_file,
                FILE_LOG_LEVEL: self.file_log_level,
                CONSOLE_LOG_LEVEL: self.console_log_level,
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
            path.basename(file): read_dicts_from_csv(file) for file in glob(path.join(self.metadata_dir, "score", "*.csv"))
        }
        if not self.scores_metadata:
            print('\nMetadata could not be loaded properly!! Check metadata path in config file.\n')
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
