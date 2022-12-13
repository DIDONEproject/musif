from pathlib import PurePath

from musif.common._logs import create_logger
from musif.common._utils import (
    read_object_from_json_file,
    read_object_from_yaml_file,
)
from musif.extract.constants import REQUIRE_MSCORE

# TODO: add documentation for these variables
LOGGER_NAME = "musiF"
LOG = "log"
LOG_FILE_PATH = "log_file"
FILE_LOG_LEVEL = "file_log_level"
CONSOLE_LOG_LEVEL = "console_log_level"
XML_DIR = "data_dir"
MUSESCORE_DIR = "musescore_dir"
CACHE_DIR = "cache_dir"
PARALLEL = "parallel"
MAX_PROCESSES = "max_processes"
FEATURES = "features"
BASIC_MODULES = "basic_modules"
BASIC_MODULES_ADDRESSES = "basic_modules_addresses"
FEATURE_MODULES_ADDRESSES = "feature_modules_addresses"
PARTS_FILTER = "parts_filter"
EXPAND_REPEATS = "expand_repeats"
WINDOW_SIZE = "window_size"
OVERLAP = "overlap"
PRECACHE_HOOKS = "precache_hooks"
MSCORE_EXEC = "mscore_exec"
# Didone specific?
SPLIT_KEYWORDS = "split_keywords"
# Didone specific
METADATA_DIR = "metadata_dir"


DELETE_FILES = "delete_failed_files"
DELETE_HARMONY = "delete_files_without_harmony"
UNBUNDLE_INSTRUMENTATION = "separate_intrumentation_column"
INSTRUMENTS_TO_KEEP = "instruments_to_keep"
INSTRUMENTS_TO_DELETE = "instruments_to_delete"
SUBSTRING_TO_DELETE = "substring_to_delete"
ENDSWITH = "columns_endswith"
STARTSWITH = "columns_startswith"
CONTAIN = "columns_contain"
REPLACE_NANS = "replace_nans"
PRESENCE = "delete_presence"
DFS_DIR = "dfs_dir"
GROUPED = "grouped_analysis"
MERGE_VOICES = "merge_voices"

_CONFIG_LOG_FALLBACK = {
    LOG_FILE_PATH: "./musiF.log",
    FILE_LOG_LEVEL: "DEBUG",
    CONSOLE_LOG_LEVEL: "INFO",
}

_CONFIG_FALLBACK = {
    XML_DIR: ".",
    MUSESCORE_DIR: None,
    CACHE_DIR: None,
    PARALLEL: False,
    MAX_PROCESSES: 1,
    PRECACHE_HOOKS: [],
    BASIC_MODULES: ["core"],
    BASIC_MODULES_ADDRESSES: ["musif.extract.basic_modules"],
    FEATURE_MODULES_ADDRESSES: ["musif.extract.features"],
    FEATURES: None,
    SPLIT_KEYWORDS: [],
    PARTS_FILTER: [],
    EXPAND_REPEATS: False,
    WINDOW_SIZE: 8,
    OVERLAP: 2,
    MSCORE_EXEC: None,
    DFS_DIR: None,
}

_CONFIG_POST_FALLBACK = {
    DELETE_FILES: False,
    GROUPED: False,
    DELETE_FILES: False,
    DELETE_HARMONY: False,
    UNBUNDLE_INSTRUMENTATION: False,
    MERGE_VOICES: True,
    INSTRUMENTS_TO_KEEP: [],
    INSTRUMENTS_TO_DELETE: [],
    SUBSTRING_TO_DELETE: [],
    PRESENCE: [],
    ENDSWITH: [],
    STARTSWITH: [],
    CONTAIN: [],
    REPLACE_NANS: [],
}



class AbstractConfiguration:
    # TODO: add documentation
    def _get_fallback(self):
        pass

    def __init__(self, arg, **kwargs):
        config_data = {}
        if arg is not None:
            if isinstance(arg, str) or isinstance(arg, PurePath):
                config_data = read_object_from_yaml_file(arg)
            elif isinstance(arg, dict):
                config_data = arg
            elif isinstance(arg, AbstractConfiguration):
                config_data = arg.to_dict()
            else:
                raise TypeError(
                    f"The argument type is {type(arg)}, and it was expected a dictionary, a Configuration or a string object"
                )
        config_data.update(kwargs)  # Override values
        log_config = config_data.get(LOG, _CONFIG_LOG_FALLBACK)
        for config in [config_data, log_config]:
            for k, v in config.items():
                if k == LOG:
                    continue
                self.__dict__[k] = v

        for fallback in [_CONFIG_LOG_FALLBACK, self._get_fallback()]:
            for k, v in fallback.items():
                if k in self.__dict__:
                    continue
                else:
                    self.__dict__[k] = v

        create_logger(
            LOGGER_NAME, self.log_file, self.file_log_level, self.console_log_level
        )

    def to_dict(self) -> dict:
        # TODO: doc
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class ExtractConfiguration(AbstractConfiguration):

    def _get_fallback(self):
        return _CONFIG_FALLBACK

    def is_requested_musescore_file(self) -> bool:
        # TODO: doc

        for feature in REQUIRE_MSCORE:
            if self.is_requested_feature_category(feature):
                return True
        return False

    def is_requested_feature_category(self, feature) -> bool:
        # TODO: doc

        if self.features is None:
            return True
        return feature in self.features

    def is_requested_module(self, module) -> bool:
        # TODO: doc

        if self.features is None:
            return True
        module_path = module.__name__
        module_name = (
            module_path
            if "." not in module_path
            else module_path[module_path.rindex(".") + 1 :]
        )
        for feature in self.features:
            if feature.lower().endswith(module_name.lower()):
                return True
        return False


class PostProcessConfiguration(AbstractConfiguration):
    def _get_fallback(self):
        return _CONFIG_POST_FALLBACK
