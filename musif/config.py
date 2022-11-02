import multiprocessing
from glob import glob
from os import path

from musif import internal_data
from musif.common._logs import create_logger
from musif.common._utils import read_dicts_from_csv, read_object_from_json_file, read_object_from_yaml_file
from musif.extract.constants import HARMONY_FEATURES, SCALE_RELATIVE_FEATURES

"""Name of the logger and folder where it will be placed."""
LOGGER_NAME = "musiF"

"""Name of they key for logger info"""
LOG = "log"

"""Path where logs will be stored"""
LOG_FILE_PATH = "file_path"

"""Constant name for the level of file logging"""
FILE_LOG_LEVEL = "file_level"

"""Constant name for the level of console logging"""
CONSOLE_LOG_LEVEL = "console_level"

"""Constant name for the folder containing metadata"""
METADATA_DIR = "metadata_dir"

"""Constant name for id metadata"""
METADATA_ID_COL = "metadata_id_col"

"""Constant name for folder containing xml files"""
DATA_DIR = "data_dir"

"""Constant name for folder containing mscx files"""
MUSESCORE_DIR = "musescore_dir"

"""Constant name for parallelization info"""
PARALLEL = "parallel"

"""Constant name maximum number of processes allowed"""
MAX_PROCESSES = "max_processes"

"""Constant name for features to be extracted"""
FEATURES = "features"

BASIC_MODULES = "basic_modules"

"""Keywords for parts that need to be splitted when sharing same staff"""
SPLIT_KEYWORDS = "split_keywords"

"""Constant name for features to be extracted"""
PARTS_FILTER = "parts_filter"

"""Constant name to expand repetitions or not"""
EXPAND_REPEATS = "expand_repeats"
WINDOW_SIZE='window_size'
OVERLAP='overlap'

"""--- Post-Processing constants--- """

"""File that keeps previously extracted files"""
CHECK_FILE = "checking_file"

"""If delete files present in errors.csv file or not"""
DELETE_FILES = "delete_failed_files"

"""If grouped features need to be created or not"""
GROUPED = "grouped_analysis"

"""Separate passions for theme A in arias"""
SPLIT_PASSSIONS = "split_passionA"

"""If Instrumentation column needs to be unbundled into several columns or not"""
UNBUNDLE_INSTRUMENTATION = "separate_intrumentation_column"

"""Constant name for instruments that need to be kept"""
INSTRUMENTS_TO_KEEP = "instruments_to_keep"

"""Constant name for instruments that need to be deleted"""
INSTRUMENTS_TO_DELETE = "instruments_to_delete"

"""Constant name for substring present in column names to drop those columns"""
SUBSTRING_TO_DELETE = "substring_to_delete"

"""Constant name for substring ending in column names to drop those columns"""
ENDSWITH = "columns_endswith"

"""Constant name for substring start in column names to drop those columns"""
STARTSWITH = "columns_startswith"

"""Constant name for string contained by column names to drop those columns"""
CONTAIN = "columns_contain"

"""Constant name for Presence_ column names that need to be droppped"""
PRESENCE = "delete_presence"
"""If the different singers names features are needed to be grouped into a single 'SoundVoice' column or not"""
MERGE_VOICES = "merge_voices"

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
    BASIC_MODULES: ["core"],
    FEATURES: None,
    SPLIT_KEYWORDS: [],
    PARTS_FILTER: [],
    EXPAND_REPEATS: False,
    WINDOW_SIZE: 8,
    OVERLAP: 2,    
    CHECK_FILE: "."
}

_CONFIG_POST_FALLBACK = {
    INTERNAL_DATA: 'musif/internal_data',
    DELETE_FILES: False,
    GROUPED: False,
    DELETE_FILES: False,
    DELETE_HARMONY: False,
    SPLIT_PASSSIONS: False,
    UNBUNDLE_INSTRUMENTATION: False,
    MERGE_VOICES: True,
    CHECK_FILE: ".",
    INSTRUMENTS_TO_KEEP: [],
    INSTRUMENTS_TO_DELETE: [],
    SUBSTRING_TO_DELETE: [],
    PRESENCE: [],
    ENDSWITH: [],
    STARTSWITH: [],
    CONTAIN: [],
    REPLACE_NANS: []
}

class Configuration:
    # TODO: add documentation
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
        self.basic_modules = config_data.get(BASIC_MODULES, _CONFIG_FALLBACK[BASIC_MODULES])
        self.features = config_data.get(FEATURES, _CONFIG_FALLBACK[FEATURES])
        self.split_keywords = config_data.get(SPLIT_KEYWORDS, _CONFIG_FALLBACK[SPLIT_KEYWORDS])
        self.parts_filter = config_data.get(PARTS_FILTER, _CONFIG_FALLBACK[PARTS_FILTER])
        self.expand_repeats = config_data.get(EXPAND_REPEATS, _CONFIG_FALLBACK[EXPAND_REPEATS])
        self.window_size = config_data.get(WINDOW_SIZE, _CONFIG_FALLBACK[WINDOW_SIZE])
        self.overlap = config_data.get(OVERLAP, _CONFIG_FALLBACK[OVERLAP])
        
        self.internal_data_dir = path.dirname(internal_data.__file__)
        self.check = config_data.get(CHECK_FILE, _CONFIG_FALLBACK[CHECK_FILE])
        self._load_metadata()

    def is_requested_musescore_file(self) -> bool:
        """
        Returns True or False to extract harmonic information depending on the modules that
        need to be analyzed, if they depend on harmonic information or not.
        """
        
        if self.is_requested_feature_category(HARMONY_FEATURES):
            return True
        if self.is_requested_feature_category(SCALE_RELATIVE_FEATURES):
            return True
        return False

    def is_requested_feature_category(self, feature) -> bool:
        """
        Returns True or False to inform if a feature has been required to be analyzed.
        If the list of required features is None, any feature will be marked as True.
        """

        if self.features is None:
            return True
        return feature in self.features

    def is_requested_module(self, module) -> bool:
        """
        Returns True or False to inform if a module has been required to be analyzed.
        If the list of required features is None, any feature will be marked as True.
        """
        
        if self.features is None:
            return True
        module_path = module.__name__
        module_name = module_path if "." not in module_path else module_path[module_path.rindex(".") + 1:]
        for feature in self.features:
            if feature.lower().endswith(module_name.lower()):
                return True
        return False

    def to_dict(self) -> dict:
        """        
        Method to throw the information of a Configuration object on a dictionary
        """

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
        self.all_translations = read_object_from_json_file(path.join(self.internal_data_dir, "all_translations.json"))
        
        self.cpu_workers = (
            multiprocessing.cpu_count() - 2 if multiprocessing.cpu_count() > 3 else multiprocessing.cpu_count() // 2
        )

class PostProcess_Configuration:
    # TODO: docuemtn this class
    # TODO: rename class without underscore

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
                config_data = args[0].to_dict_post()
            else:
                raise TypeError(f"The argument type is {type(args[0])}, and it was expected a dictionary, a Configuration or a string object")
        config_data.update(kwargs)  # Override values
        log_config = config_data.get(LOG, _CONFIG_FALLBACK[LOG])
        self.log_file = log_config.get(LOG_FILE_PATH, _CONFIG_FALLBACK.get(LOG_FILE_PATH))
        self.file_log_level = log_config.get(FILE_LOG_LEVEL, _CONFIG_FALLBACK.get(FILE_LOG_LEVEL))
        self.console_log_level = log_config.get(CONSOLE_LOG_LEVEL, _CONFIG_FALLBACK.get(CONSOLE_LOG_LEVEL))
        create_logger(LOGGER_NAME, self.log_file, self.file_log_level, self.console_log_level)
        
        self.internal_data = config_data.get(INTERNAL_DATA, _CONFIG_POST_FALLBACK[INTERNAL_DATA])
        self.check_file = config_data.get(CHECK_FILE, _CONFIG_POST_FALLBACK[CHECK_FILE])
        self.delete_files = config_data.get(DELETE_FILES, _CONFIG_POST_FALLBACK[DELETE_FILES])
        self.grouped_analysis = config_data.get(GROUPED, _CONFIG_POST_FALLBACK[GROUPED])
        self.split_passionA = config_data.get(SPLIT_PASSSIONS, _CONFIG_POST_FALLBACK[SPLIT_PASSSIONS])
        self.unbundle_instrumentation = config_data.get(UNBUNDLE_INSTRUMENTATION, _CONFIG_POST_FALLBACK[UNBUNDLE_INSTRUMENTATION])
        self.merge_voices = config_data.get(MERGE_VOICES, _CONFIG_POST_FALLBACK[MERGE_VOICES])
        self.instruments_to_keep = config_data.get(INSTRUMENTS_TO_KEEP, _CONFIG_POST_FALLBACK[INSTRUMENTS_TO_KEEP])
        self.instruments_to_kill = config_data.get(INSTRUMENTS_TO_DELETE, _CONFIG_POST_FALLBACK[INSTRUMENTS_TO_DELETE])
        self.substring_to_kill = config_data.get(SUBSTRING_TO_DELETE, _CONFIG_POST_FALLBACK[SUBSTRING_TO_DELETE])
        self.delete_presence = config_data.get(PRESENCE, _CONFIG_POST_FALLBACK[PRESENCE])        
        self.columns_endswith = config_data.get(ENDSWITH, _CONFIG_POST_FALLBACK[ENDSWITH])
        self.columns_startswith = config_data.get(STARTSWITH, _CONFIG_POST_FALLBACK[STARTSWITH])
        self.columns_contain = config_data.get(CONTAIN, _CONFIG_POST_FALLBACK[CONTAIN])
        self.replace_nans = config_data.get(REPLACE_NANS, _CONFIG_POST_FALLBACK[REPLACE_NANS])
        self.delete_files_without_harmony = config_data.get(DELETE_HARMONY, _CONFIG_POST_FALLBACK[DELETE_HARMONY])
        
    def to_dict_post(self) -> dict:
        return {
        LOG: {
            LOG_FILE_PATH: self.log_file,
            FILE_LOG_LEVEL: self.file_log_level,
            CONSOLE_LOG_LEVEL: self.console_log_level,
        },
        CHECK_FILE: self.check_file,
        DELETE_FILES: self.delete_files,
        GROUPED: self.grouped_analysis,
        SPLIT_PASSSIONS: self.split_passionA,
        INSTRUMENTS_TO_KEEP: self.instruments_to_keep,
        INSTRUMENTS_TO_DELETE: self.instruments_to_kill,
        SUBSTRING_TO_DELETE: self.substring_to_kill,
        ENDSWITH: self.columns_endswith,
        STARTSWITH: self.columns_startswith,
        CONTAIN: self.columns_contain,
        PRESENCE: self.delete_presence,
        REPLACE_NANS: self.replace_nans,

    }


