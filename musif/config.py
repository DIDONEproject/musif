from pathlib import PurePath

from musif.common._logs import create_logger
from musif.common._utils import read_object_from_yaml_file
from musif.extract.constants import REQUIRE_MSCORE

"""Check config_extraction_example.yml file for the purpose of these variables, if needed."""
LOGGER_NAME = "musif"
LOG = "log"
LOG_FILE_PATH = "log_file"
FILE_LOG_LEVEL = "file_log_level"
CONSOLE_LOG_LEVEL = "console_log_level"
data_dir = "data_dir"
MUSESCORE_DIR = "musescore_dir"
CACHE_DIR = "cache_dir"
IGNORE_ERRORS = "ignore_errors"
PARALLEL = "parallel"
FEATURES = "features"
BASIC_MODULES = "basic_modules"
BASIC_MODULES_ADDRESSES = "basic_modules_addresses"
FEATURE_MODULES_ADDRESSES = "feature_modules_addresses"
PARTS_FILTER = "parts_filter"
EXPAND_REPEATS = "expand_repeats"
WINDOW_SIZE = "window_size"
OVERLAP = "overlap"
PRECACHE_HOOKS = "precache_hooks"
REMOVE_UNPITCHED_OBJECTS = "remove_unpitched_objects"
MSCORE_EXEC = "mscore_exec"
SPLIT_KEYWORDS = "split_keywords"

DELETE_FILES = "delete_failed_files"
DELETE_HARMONY = "delete_files_without_harmony"

UNBUNDLE_INSTRUMENTATION = "separate_intrumentation_column"
INSTRUMENTS_TO_KEEP = "instruments_to_keep"
INSTRUMENTS_TO_DELETE = "instruments_to_delete"
ENDSWITH = "columns_endswith"
STARTSWITH = "columns_startswith"
CONTAIN = "columns_contain"
MATCH = "columns_match"
REPLACE_NANS = "replace_nans"
DFS_DIR = "dfs_dir"
GROUPED = "grouped_analysis"
MERGE_VOICES = "merge_voices"
MAX_NAN_COLUMNS = "max_nan_columns"
MAX_NAN_ROWS = "max_nan_rows"
DELETE_COLUMNS_WITH_NANS = "delete_columns_with_nans"

_CONFIG_LOG_FALLBACK = {
    LOG_FILE_PATH: "./musif.log",
    FILE_LOG_LEVEL: "DEBUG",
    CONSOLE_LOG_LEVEL: "ERROR",
}

_CONFIG_FALLBACK = {
    data_dir: None,
    MUSESCORE_DIR: None,
    CACHE_DIR: None,
    PARALLEL: 1,
    PRECACHE_HOOKS: [],
    BASIC_MODULES: [],
    IGNORE_ERRORS: False,
    BASIC_MODULES_ADDRESSES: ["musif.extract.basic_modules"],
    FEATURE_MODULES_ADDRESSES: ["musif.extract.features"],
    FEATURES: ["core"],
    SPLIT_KEYWORDS: [],
    PARTS_FILTER: [],
    EXPAND_REPEATS: False,
    WINDOW_SIZE: None,
    OVERLAP: 2,
    MSCORE_EXEC: None,
    DFS_DIR: None,
    REMOVE_UNPITCHED_OBJECTS: True,
}

_CONFIG_POST_FALLBACK = {
    DELETE_FILES: False,
    GROUPED: False,
    DELETE_FILES: False,
    DELETE_HARMONY: False,
    UNBUNDLE_INSTRUMENTATION: False,
    MERGE_VOICES: True,
    DELETE_COLUMNS_WITH_NANS: True,
    INSTRUMENTS_TO_KEEP: [],
    INSTRUMENTS_TO_DELETE: [],
    ENDSWITH: [],
    STARTSWITH: [],
    CONTAIN: [],
    REPLACE_NANS: [],
    MATCH: [],
    MAX_NAN_COLUMNS: None,
    MAX_NAN_ROWS: None
}


class GenericConfiguration:
    """
    Generic class for configuration objects.

    When subclassing, you should override the `_get_fallback` method.
    """

    def _get_fallback(self):
        """
        Returns a dictionary containing the default values for this configuration
        object. Such values will be always available, but can be overriden by the
        user.
        """
        return {}

    def __init__(self, arg, **kwargs):
        """
        It set up the `Configuration` object in this way:

            #. it sets the default values returned by `self._get_fallback()` as filed of
               the object (i.e. in the `__dict__` dictionary)
            #. it load the configuration file `arg` provided by the user
            #. it overrides the configuration file with the keyword arguments
            #. it sets the values obtained, overriding the one already available, in
               `__dict_`, making them avilable as usual fields
        """
        # set default values
        for fallback in [_CONFIG_LOG_FALLBACK, self._get_fallback()]:
            for k, v in fallback.items():
                self.__dict__[k] = v

        # load configuration file
        config_data = {}
        if arg is not None:
            if isinstance(arg, str) or isinstance(arg, PurePath):
                config_data = read_object_from_yaml_file(arg)
            elif isinstance(arg, dict):
                config_data = arg
            elif isinstance(arg, GenericConfiguration):
                config_data = arg.to_dict()
            else:
                raise TypeError(
                    f"The argument type is {type(arg)}, and it was expected a dictionary, a Configuration or a string object"
                )

        # override values with kwargs
        config_data.update(kwargs)
        log_config = config_data.get(LOG, {})
        for config in [config_data, log_config]:
            for k, v in config.items():
                if k == LOG:
                    continue
                self.__dict__[k] = v

        create_logger(
            LOGGER_NAME, self.log_file, self.file_log_level, self.console_log_level
        )

    def to_dict(self) -> dict:
        """
        Returns a dictionary having as keys the public fields of this object.
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class ExtractConfiguration(GenericConfiguration):
    """
    Configuration object used by :class: `musif.extract.extract.FeatureExtractor`

    It additionaly sets the following properties:

    ..  code-block:: python

        from musif.musicxml import constants as musicxml_c
        self.scoring_family_order = musicxml_c.SCORING_FAMILY_ORDER
        self.scoring_order = musicxml_c.SCORING_ORDER
        self.sound_to_family = musicxml_c.SOUND_TO_FAMILY
        self.family_to_abbreviation = musicxml_c.FAMILY_TO_ABBREVIATION
        self.sound_to_abbreviation = musicxml_c.SOUND_TO_ABBREVIATION

    The above settings can be overriden by the user both by changing
    the variables in `musicxml.constants` and by adding them to the configuration.
    """

    def __init__(self, *args, **kwargs):
        from musif.musicxml import constants as musicxml_c
        # ^--- here to avoid circular imports
        self.scoring_family_order = musicxml_c.SCORING_FAMILY_ORDER
        self.scoring_order = musicxml_c.SCORING_ORDER
        self.sound_to_family = musicxml_c.SOUND_TO_FAMILY
        self.family_to_abbreviation = musicxml_c.FAMILY_TO_ABBREVIATION
        self.sound_to_abbreviation = musicxml_c.SOUND_TO_ABBREVIATION
        super().__init__(*args, **kwargs)

    def _get_fallback(self):
        return _CONFIG_FALLBACK

    def is_requested_musescore_file(self) -> bool:
        """
        Returns `True` if any of the requested features needs musescore files for the
        harmonic annotations.
        Returns `False` otherwise.
        """

        for feature in REQUIRE_MSCORE:
            if self.is_requested_feature_category(feature):
                return True
        return False

    def is_requested_feature_category(self, feature: str) -> bool:
        """
        Returns `True` if `feature` is among the requeste features, according to the
        configuration.
        Returns `False` otherwise.
        """

        if self.features is None:
            return True
        return feature in self.features


class PostProcessConfiguration(GenericConfiguration):
    """
    Configuration object used by :class: `musif.process.DataProcessor`
    """

    def _get_fallback(self):
        return _CONFIG_POST_FALLBACK
