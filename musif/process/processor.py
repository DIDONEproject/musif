import os
import re
from pathlib import PurePath
from typing import Union
import numpy as np

import pandas as pd
from pandas import DataFrame

from musif.common.sort import sort_columns
from musif.config import PostProcessConfiguration
from musif.extract.basic_modules.file_name_generic.constants import ARTIST, TITLE
from musif.extract.basic_modules.scoring.constants import (
    INSTRUMENTATION,
    NUMBER_OF_FILTERED_PARTS,
    NUMBER_OF_PARTS,
)
from musif.extract.constants import ID, WINDOW_ID
from musif.extract.features.core.constants import (
    FILE_NAME,
    NOTES_MEAN,
    NUM_NOTES,
    SOUNDING_MEASURES_MEAN,
)
from musif.extract.features.harmony.constants import (
    ADDITIONS_prefix,
    APPLIED_prefix,
    CHORD_prefix,
    CHORDS_GROUPING_prefix,
    HARMONY_AVAILABLE,
    HARMONY_PREFIX,
    KEY_MODULATORY,
    KEY_PREFIX,
    NUMERALS_prefix,
)
from musif.logs import perr, pinfo
from musif.process.constants import PRESENCE
from musif.process.utils import (
    _delete_columns,
    join_keys,
    join_keys_modulatory,
    join_part_degrees,
)


# Columns that count events or give their proportion: an empty cell there can
# stand for "no such event". Everything else is a statistic (a mean, a
# deviation, a ratio, an extreme...), for which an empty cell means that the
# value does not exist.
_EVENT_SUFFIX = re.compile(r"(_Count|_Per)(_relative)?$")
_HARMONY_EVENT_PREFIXES = (
    KEY_PREFIX,
    CHORD_prefix,
    CHORDS_GROUPING_prefix,
    NUMERALS_prefix,
    ADDITIONS_prefix,
    APPLIED_prefix,
)
# The scope a column describes: one part, sound or family, the whole score, or
# the harmonic analysis.
_SCOPE = re.compile(r"^((?:Part|Sound|Family)[^_|]+|Score|Harmony)_")


def _counts_events(column: str) -> bool:
    return (
        _EVENT_SUFFIX.search(column) is not None
        or column.startswith(_HARMONY_EVENT_PREFIXES)
        or column.startswith(PRESENCE)
    )


class DataProcessor:
    """Processor class that treats columns and information of a DataFrame

    This operator processes information from a DataFrame or a .csv file.
    It deletes unseful columns for analysis and saves important ones.
    Also saves data in several files in .csv format.
    The main method .process() returns a DataFrame and saves data.
    Requires to have a labels file in ./internal_data directory containing
    each label assigned to each score.
    ...

    Attributes
    ----------
    data : DataFrame
        DataFrame extracted with FeaturesExtractor containing all info.
    info: str
        Path to .csv file or Dataframe containing the information from FeaturesExtractor
    """

    def __init__(self, info: Union[str, DataFrame], *args, **kwargs):
        """
        Parameters
        ----------
        *args:  str
            Could be a path to a .yml file, a PostProcessConfiguration object or a
            dictionary. Length zero or one.
        *kwargs : str
            Key words arguments to construct
        kwargs[info]: Union[str, DataFrame]
            Either a path to a .csv file containing the information either a DataFrame
            object fromm FeaturesExtractor
        """
        self._post_config = PostProcessConfiguration(*args, **kwargs)
        self.info = info
        self.data = self._process_info(self.info)

    def _process_info(self, info: Union[str, DataFrame]) -> DataFrame:
        """
        Extracts the info from a directory to a csv file or from a Dataframe object.

        Parameters
        ------
        info: str
            Info in the from of str (path to csv file) or DataFrame

        Raises
        ------
        FileNotFoundError
            If path to the .csv file is not found.

        Returns
        ------
            Dataframe contaning the information to be processed.
        """

        try:
            if isinstance(info, str) or isinstance(info, PurePath):
                pinfo(f"\nReading csv file {info}...")
                if not os.path.exists(info):
                    raise FileNotFoundError("A .csv file could not be found")
                if isinstance(info, PurePath):
                    self.destination_route = str(info.with_suffix(""))
                else:
                    self.destination_route = info.replace(".csv", "")
                df = pd.read_csv(
                    info, low_memory=False, sep=",", encoding_errors="replace"
                )
                if df.empty:
                    raise FileNotFoundError("The .csv file could not be found.")
                return df

            elif isinstance(info, DataFrame):
                return info
            else:
                perr(
                    "Wrong info type! You must introduce either a DataFrame either the name of a .csv file."
                )
                return pd.DataFrame()

        except OSError as e:
            perr(
                f"Data could not be loaded. Either wrong path or an empty file was found. {e}"
            )
            return e

    def process(self) -> DataFrame:
        """
        Main method of the class. Removes NaN values, deletes unuseful columns
        and merges those that are needed according to config.yml file.

        Returns
        ------
        Dataframe object
        """

        pinfo("\nPost-processing data...")
        self.data.dropna(axis=1, how="all", inplace=True)
        if self._post_config.delete_files_without_harmony:
            self.delete_files_without_harmony()
        if self._post_config.separate_instrumentation_column:
            pinfo('\nSeparating "Instrumentation" column...')
            self.separate_instrumentation_column()

        # An empty cell is replaced by 0 only where 0 is the measured value:
        # an event that did not happen in a part that does play (see
        # replace_nans). The cells of a part that is not in the score, and
        # the statistics that do not exist, stay empty, so the NaN thresholds
        # that follow (max_nan_rows, max_nan_columns) judge exactly that: how
        # often there was nothing to measure.
        self.replace_nans()
        self.delete_undesired()
        if self._post_config.delete_duplicated_sound_columns:
            self.delete_duplicated_sound_columns()

        if self._post_config.grouped_analysis:
            self.group_columns()
        self.data.reset_index(inplace=True)
        self._final_data_processing()
        return self

    def delete_duplicated_sound_columns(self) -> None:
        """
        Deletes the ``Sound<X>_*`` columns of every sound performed by exactly
        one part throughout the DataFrame: for a single-part sound they equal
        the ``Part<X>_*`` columns by construction (the sound scope aggregates
        over one part). The per-part-mean and part-count columns
        (``NotesMean``, ``SoundingMeasuresMean``, ``NumberOfParts``,
        ``NumberOfFilteredParts``) are kept.
        """
        spared = (
            NOTES_MEAN,
            SOUNDING_MEASURES_MEAN,
            NUMBER_OF_PARTS,
            NUMBER_OF_FILTERED_PARTS,
        )
        sounds = {
            col[len("Sound"):].split("_", 1)[0]
            for col in self.data.columns
            if col.startswith("Sound") and "_" in col
        }
        to_delete = []
        for sound in sorted(sounds):
            prefix = f"Sound{sound}_"
            parts_col = prefix + NUMBER_OF_PARTS
            if parts_col not in self.data.columns:
                continue
            n_parts = self.data[parts_col].dropna()
            if len(n_parts) == 0 or n_parts.max() != 1:
                continue
            to_delete += [
                col
                for col in self.data.columns
                if col.startswith(prefix) and not col.endswith(spared)
            ]
        if to_delete:
            pinfo(
                f"\nDeleting {len(to_delete)} single-part Sound columns "
                "duplicating their Part columns..."
            )
            self.data.drop(columns=to_delete, inplace=True, errors="ignore")

    def delete_files_without_harmony(self):
        """
        Deletes files (actually rows in the DataFrame) that didn't have a proper
        harmonic analysis and, there fore, got a value of 0 in 'Harmony_Available'
        column
        """
        if HARMONY_AVAILABLE in self.data:
            number_files = len(self.data[self.data[HARMONY_AVAILABLE] == 0])
            if number_files > 0:
                pinfo(
                    f"{number_files} file(s) were found without mscx analysis or errors in harmonic analysis. They'll be deleted from the df"
                )
                pinfo(f"{self.data[self.data[HARMONY_AVAILABLE] == 0][FILE_NAME].to_string()}")
            mask = (self.data[HARMONY_AVAILABLE] == 0)
            self.data = self.data[~mask]           
        else:
                pinfo(f"No files were found without harmonic analysis!")
                
    def group_columns(self) -> None:
        """
        Groups Key_*_PercentageMeasures, Key_Modulatory and Degrees columns. Into bigger
        groups for agregated analysis, keeping the previous ones. Also deletes
        unnecesary columns for analysis.
        """
        try:
            self._group_keys_modulatory()
            self._group_keys()
            self._join_degrees()
            self._join_degrees_relative()
        except KeyError:
            perr("Some columns to group could not be found.")

    def separate_instrumentation_column(self) -> None:
        """
        Separates Instrumentation column into as many columns as instruments present in
        Instrumentation, assigning a value of 1 for every instrument that is present and
        0 if it is not for every row (aria).
        """
        # iterate by index LABEL: positional .at[] corrupted the frame after
        # row deletions and on windowed (MultiIndex) data
        for label, row in self.data[INSTRUMENTATION].items():
            if str(row) != 'nan':
                for element in row.split(","):
                    self.data.at[label, PRESENCE + "_" + element] = 1
        self.data[[i for i in self.data if PRESENCE + "_" in i]] = (
            self.data[[i for i in self.data if PRESENCE + "_" in i]]
            .fillna(0)
            .astype(int)
        )

    def delete_undesired(self, **kwargs) -> None:
        """Deletes not necessary columns and rows for statistical analysis.

        If keyword arguments are passed in, they overwrite those found
        into configurationg file

        Parameters
        ----------
        **kwargs : str, optional
            Any value from config.yml can be overwritten by passing arguments
            to the method

        Raises
        ------
        KeyError
            If any of the columns required to delete is not found
            in the original DataFrame.
        """
        config_data = self._post_config.__dict__
        config_data.update(kwargs)  # Override values

        # deleting columns that are completely nans
        idx = self.data.isna().all()
        to_delete = self.data.columns[idx].to_list()
        self.data.drop(columns=to_delete, inplace=True)

        # Deleting rows
        th = config_data["max_nan_rows"] or 1.0
        idx = self.data.isna().sum(axis=1) / self.data.shape[1] > th
        to_delete = self.data.index[idx]
        self.data.drop(index=to_delete, inplace=True)

        _delete_columns(self.data, config_data)

    def replace_nans(self) -> None:
        """
        Replaces by 0 the empty cells that stand for "no such event".

        Only the columns selected by `replace_nans` in the configuration are
        touched, and among them only those that count events or give their
        proportion (`_Count`, `_Per`, and the chord, numeral, key and addition
        columns of the harmonic analysis). A cell is replaced only in the rows
        where there was something to measure: the part, sound or family has
        notes in that score, and, for the columns that depend on the harmonic
        analysis (`Harmony_` and `_relative`), the analysis is available.

        So after this step a 0 is always a measured zero. The cells of a part
        that is absent from a score stay empty, and so do the statistics
        (means, deviations, ratios...) that could not be computed.
        """
        substrings = self._post_config.replace_nans
        if not substrings:
            return
        numeric = set(self.data.select_dtypes(include="number").columns)
        columns = [
            col
            for col in self.data.columns
            if col in numeric
            and _counts_events(col)
            and any(substring.lower() in col.lower() for substring in substrings)
        ]
        if not columns:
            return

        presence = {}

        def measured(scope, needs_analysis):
            key = (scope, needs_analysis)
            if key not in presence:
                rows = pd.Series(True, index=self.data.index)
                if scope is not None and scope != HARMONY_PREFIX.rstrip("_"):
                    rows &= self._has_notes(scope, numeric)
                if needs_analysis:
                    rows &= self._has_analysis(scope, numeric)
                presence[key] = rows
            return presence[key]

        filled = {}
        for col in columns:
            match = _SCOPE.match(col)
            scope = match.group(1) if match else None
            needs_analysis = col.startswith(HARMONY_PREFIX) or col.endswith("_relative")
            rows = measured(scope, needs_analysis)
            filled[col] = self.data[col].where(self.data[col].notna() | ~rows, 0)
        self.data[columns] = pd.DataFrame(filled, index=self.data.index)

    def _has_notes(self, scope: str, numeric: set) -> pd.Series:
        """Rows in which the part, sound or family `scope` has any note."""
        notes = f"{scope}_{NUM_NOTES}"
        if notes in numeric:
            return self.data[notes].fillna(0) > 0
        # without the note count, a scope counts as present where any of its
        # columns holds a value
        columns = [col for col in numeric if col.startswith(scope + "_")]
        return self.data[columns].notna().any(axis=1)

    def _has_analysis(self, scope, numeric: set) -> pd.Series:
        """Rows for which the harmonic analysis was extracted."""
        if HARMONY_AVAILABLE in self.data.columns:
            return self.data[HARMONY_AVAILABLE] == 1
        # without the flag, the analysis counts as available where any column
        # that depends on it holds a value
        columns = [
            col
            for col in numeric
            if col.startswith(HARMONY_PREFIX) or col.endswith("_relative")
        ]
        return self.data[columns].notna().any(axis=1)

    def save(
        self, dest_path: Union[str, PurePath], ext=".csv", ft="csv", **kwargs
    ) -> None:
        """Saves current information into a file given the name of dest_path

        To load one of those file, remember to set the index to
        `musif.extract.constant.ID`, and, if windows are used, to
        `musif.extract.constant.WINDOW_ID`:

        ```python
        df = pd.read_csv('window_alldata.csv').set_index(['Id', 'WindowId'])
        ```

        Parameters
        ----------
        dest_path : str or Path
            Path to directory where the file will be stored; the suffix
            `_alldata` plus the extension is added.
        ext : str
            Extension used to save files. Use `.gz`, `.xz`, `.zip` etc. to compress the
            files. Default: `.csv`
        ft : str
            Type of file for saving. The filetype must be supported by `pandas`, e.g.
            `to_csv`, `to_feather`, `to_parquet`, etc. Default: `csv`
        """

        pinfo(f"Writing data to {dest_path}_*{ext}")
        dest_path = str(dest_path)
        if ft == "csv":
            kwargs.setdefault("index", False)
        ft = "to_" + ft
        getattr(self.data, ft)(dest_path + "_alldata" + ext, **kwargs)

    def _group_keys_modulatory(self) -> None:
        self._group_key_columns(
            join_keys_modulatory,
            lambda col: KEY_PREFIX + KEY_MODULATORY in col,
        )

    def _group_keys(self) -> None:
        self._group_key_columns(join_keys, lambda col: KEY_PREFIX in col)

    def _group_key_columns(self, join, selects) -> None:
        columns = [col for col in self.data.columns if selects(col)]
        # a score without harmonic analysis has no key areas at all: its
        # cells, and the groups built from them, stay empty
        analysed = self.data[columns].notna().any(axis=1)
        self.data.loc[analysed, columns] = self.data.loc[analysed, columns].fillna(0)
        join(self.data)
        columns = [col for col in self.data.columns if selects(col)]
        self.data.loc[~analysed, columns] = np.nan

    def _join_degrees(self) -> None:
        total_degrees = [
            i for i in self.data.columns if "_Degree" in i and "relative" not in i
        ]

        for prefix in self._degree_prefixes(total_degrees):
            join_part_degrees(total_degrees, prefix, self.data)

    def _join_degrees_relative(self) -> None:
        total_degrees = [
            i for i in self.data.columns if "_Degree" in i and "relative" in i
        ]

        for prefix in self._degree_prefixes(total_degrees):
            join_part_degrees(total_degrees, prefix, self.data, sufix="_relative")

    @staticmethod
    def _degree_prefixes(total_degrees) -> list:
        """Scope prefixes (PartVnI_, Score_, ...) that actually carry degree
        columns, so grouping covers every present scope and no phantom ones."""
        return sorted({col.split("Degree", 1)[0] for col in total_degrees if col.split("Degree", 1)[0]})

    def _final_data_processing(self) -> None:
        self.data.sort_values([ID, WINDOW_ID], inplace=True)
        self.data = self.data.reindex(sorted(self.data.columns), axis=1)
        if TITLE in self.data.columns and ARTIST in self.data.columns:
            priority_columns = [FILE_NAME, TITLE, ARTIST]
        else:
            priority_columns = []
        self.data = sort_columns(self.data, [ID, WINDOW_ID] + priority_columns)
        self.data.drop(
            columns=["index", "level_0", "level_1"], inplace=True, errors="ignore"
        )
