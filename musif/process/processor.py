import os
from pathlib import PurePath
from typing import Union
import numpy as np

import pandas as pd
from pandas import DataFrame

from musif.common.sort import sort_columns
from musif.config import PostProcessConfiguration
from musif.extract.basic_modules.file_name_generic.constants import ARTIST, TITLE
from musif.extract.basic_modules.scoring.constants import INSTRUMENTATION
from musif.extract.constants import ID, WINDOW_ID
from musif.extract.features.core.constants import FILE_NAME
from musif.extract.features.harmony.constants import (
    HARMONY_AVAILABLE,
    KEY_MODULATORY,
    KEY_PREFIX,
)
from musif.extract.features.prefix import get_part_prefix, get_sound_prefix
from musif.logs import perr, pinfo
from musif.process.constants import PRESENCE
from musif.process.utils import (
    _delete_columns,
    join_keys,
    join_keys_modulatory,
    join_part_degrees,
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
        if self._post_config.separate_intrumentation_column:
            pinfo('\nSeparating "Instrumentation" column...')
            self.separate_instrumentation_column()

        self.delete_undesired()

        if self._post_config.grouped_analysis:
            self.group_columns()
        self.data.reset_index(inplace=True)
        self._final_data_processing()
        return self

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
        for i, row in enumerate(self.data[INSTRUMENTATION]):
            if str(row) != 'nan':
                for element in row.split(","):
                    self.data.at[i, PRESENCE + "_" + element] = 1
            else:
                pass
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
        # pinfo("Replacing NaN values in selected columns")
        cols = []
        
        for col in self.data.columns:
            if self._post_config.replace_nans is not None and any(
                substring.lower() in col.lower()
                for substring in tuple(self._post_config.replace_nans)
            ):
                cols.append(col)
        cols = self.data[cols].select_dtypes(include="number").columns
        self.data[cols] = self.data[cols].fillna(0)

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
            Path to directory where the file will be stored; a suffix like
            `_metadata.csv` will be added.
        ext : str
            Extension used to save files. Use `.gz`, `.xz`, `.zip` etc. to compress the
            files. Default: `.csv`
        ft : str
            Type of file for saving. The filetype must be supported by `pandas`, e.g.
            `to_csv`, `to_feather`, `to_parquet`, etc. Default: `csv`
        """

        pinfo(f"Writing data to {dest_path}_*{ext}")
        ft = "to_" + ft
        dest_path = str(dest_path)
        if ft == "csv":
            kwargs["index"] = False
        getattr(self.data, ft)(dest_path + "_alldata" + ext, **kwargs)

    def _group_keys_modulatory(self) -> None:
        self.data.update(
            self.data[
                [i for i in self.data.columns if KEY_PREFIX + KEY_MODULATORY in i]
            ].fillna(0)
        )
        join_keys_modulatory(self.data)

    def _group_keys(self) -> None:
        self.data.update(
            self.data[[i for i in self.data.columns if KEY_PREFIX in i]].fillna(0)
        )
        join_keys(self.data)

    def _join_degrees(self) -> None:
        total_degrees = [
            i for i in self.data.columns if "_Degree" in i and "relative" not in i
        ]

        for part in self._post_config.instruments_to_keep:
            join_part_degrees(total_degrees, get_part_prefix(part), self.data)
        join_part_degrees(total_degrees, get_sound_prefix("voice"), self.data)

    def _join_degrees_relative(self) -> None:
        total_degrees = [
            i for i in self.data.columns if "_Degree" in i and "relative" in i
        ]

        for part in self._post_config.instruments_to_keep:
            join_part_degrees(
                total_degrees, get_part_prefix(part), self.data, sufix="_relative"
            )
        join_part_degrees(
            total_degrees, get_sound_prefix("voice"), self.data, sufix="_relative"
        )

    def _final_data_processing(self) -> None:
        self.data.sort_values([ID, WINDOW_ID], inplace=True)
        self.replace_nans()
        self.data = self.data.reindex(sorted(self.data.columns), axis=1)
        if TITLE and ARTIST in self.data.columns:
            priority_columns = [FILE_NAME, TITLE, ARTIST]
        else:
            priority_columns = []
        self.data = sort_columns(self.data, [ID, WINDOW_ID] + priority_columns)
        self.data.drop("index", axis=1, inplace=True, errors="ignore")
