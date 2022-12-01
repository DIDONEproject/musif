import os
from collections import Counter
from pathlib import PurePath
from typing import Union

import pandas as pd
from pandas import DataFrame
from tqdm import tqdm

from musif.common._utils import read_dicts_from_csv
from musif.common.sort import sort_columns
from musif.config import PostProcess_Configuration
from musif.extract.constants import WINDOW_ID, ID
from musif.extract.basic_modules.file_name.constants import ARIA_LABEL
from musif.extract.basic_modules.scoring.constants import (
    INSTRUMENTATION,
)
from musif.extract.features.core.constants import FILE_NAME
from musif.extract.features.harmony.constants import (
    HARMONY_AVAILABLE,
    KEY_MODULATORY,
    KEY_PREFIX,
)
from musif.extract.features.prefix import get_part_prefix, get_sound_prefix
from musif.logs import perr, pinfo, pwarn
from musif.process.constants import (
    PRESENCE,
    label_by_col,
    metadata_columns,
    priority_columns,
)
from musif.process.utils import (
    delete_columns,
    join_keys,
    join_keys_modulatory,
    join_part_degrees,
)

LABELS_FILE = "Passions.csv"
MAIN_LABEL = "Label_BasicPassion"
ScoreLabel = "AriaLabel"

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

    Methods
    -------
    process_info(info=info: Union[str, DataFrame])
        Reads info and returns a DataFrame
    process()
        Processes all the DataFrame information
    assign_labels()
        Assigns labels from labels file to DataFrame according to ScoreLabel column
    preprocess_data()
        Deletes columns with no information, convertes 0 to nan and depurates data
    group_columns()
        Groups thos columns related to Keys, Key_Modulatory and Degree for agregated analysis
    unbundle_instrumentation()
        Separates 'Instrumentation' column into several Presence_ columns for every instrument present in Instrumentation.
    delete_undesired_columns(**kwargs)
        Deletes all columns that are not needed according to config.yml file  
    save(dest_path: str)
        Saves final information to various csv files, splitting data, metadata and
        features
    """

    def __init__(self, info: Union[str, DataFrame], *args, **kwargs):
        """
        Parameters
        ----------
        *args:  str
            Could be a path to a .yml file, a PostProcess_Configuration object or a dictionary. Length zero or one.
        *kwargs : str
            Key words arguments to construct
        kwargs[info]: Union[str, DataFrame]
            Either a path to a .csv file containing the information either a DataFrame object fromm FeaturesExtractor
        """
        self._post_config = PostProcess_Configuration(*args, **kwargs)
        self.info = info
        self.data = self._process_info(self.info)
        self.internal_data_dir = self._post_config.internal_data


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
                pinfo("\nReading csv file...")
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
                pinfo("\nProcessing DataFrame...")
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
        Saves processed DataFrame into a csv file if the input was a path to a file.

        Returns
        ------
        Dataframe object
        """

        pinfo("\nPreprocessing data...")
        self.preprocess_data()
        if self._post_config.delete_files_without_harmony:
            self.delete_files_without_harmony()

        if self._post_config.unbundle_instrumentation:
            pinfo('\nSeparating "Instrumentation" column...')
            self.unbundle_instrumentation()

        self.delete_undesired_columns()

        if self._post_config.grouped_analysis:
            self.group_columns()

        self._final_data_processing()
        return self.data

    def delete_files_without_harmony(self):
        """Deletes files (actually rows in the DataFrame) that didn't have a proper harmonic analysis and, there fore, got a value of 0 in
        'Harmony_Available' column"""
        if HARMONY_AVAILABLE in self.data:
            number_files = len(self.data[self.data[HARMONY_AVAILABLE] == 0])
            pinfo(
                f"{number_files} files were found without mscx analysis or errors in harmonic analysis. They'll be deleted."
            )
            pinfo(
                f"{self.data[self.data[HARMONY_AVAILABLE] == 0][FILE_NAME].to_string()}"
            )

    def assign_labels(self) -> None:
        labels = read_dicts_from_csv(
            os.path.join(self.internal_data_dir, LABELS_FILE)
        )
        data_by_aria_label = {
            label_data["Label"]: label_data for label_data in labels
        }
        for col, label in label_by_col.items():
            values = []
            for _, row in self.data.iterrows():
                data_by_aria = data_by_aria_label.get(row[ARIA_LABEL])
                label_value = data_by_aria[col] if data_by_aria else None
                values.append(label_value)
            self.data[label] = values

    def preprocess_data(self) -> None:
        """Adds labels to scores. Cleans data and removes columns with no information or rows without assigned Label"""
        self.assign_labels()
        print(
            "Deleted scores without a label: ",
            self.data[self.data[MAIN_LABEL].isnull()].shape[0],
        )
        self.data = self.data[~self.data[MAIN_LABEL].isnull()]
        self.data.dropna(axis=1, how="all", inplace=True)

    def group_columns(self) -> None:
        """Groups Key_*_PercentageMeasures, Key_Modulatory and Degrees columns. Into bigger groups
        for agregated analysis, keeping the previous ones. Also deletes unnecesary columns for analysis.
        """
        try:
            self._group_keys_modulatory()
            self._group_keys()
            self._join_degrees()
            self._join_degrees_relative()
        except KeyError:
            perr("Some columns to group could not be found.")

    def unbundle_instrumentation(self) -> None:
        """Separates Instrumentation column into as many columns as instruments present in Instrumentation,
        assigning a value of 1 for every instrument that is present and 0 if it is not for every row (aria).
        """
        for i, row in enumerate(self.data[INSTRUMENTATION]):
            for element in row.split(","):
                self.data.at[i, PRESENCE + "_" + element] = 1

        self.data[[i for i in self.data if PRESENCE + "_" in i]] = (
            self.data[[i for i in self.data if PRESENCE + "_" in i]]
            .fillna(0)
            .astype(int)
        )

    def delete_previous_items(self) -> None:
        """Deletes items from 'errors.csv' file in case they were not extracted properly"""
        # TODO: this is definitely ugly
        pinfo("\nDeleting items with errors...")
        errors_file = r"./internal_data/errors.csv"
        if os.path.exists(errors_file):
            errors = pd.read_csv(
                errors_file, low_memory=False, encoding_errors="replace", header=0
            )[FILE_NAME].tolist()
            for item in errors:
                index = self.data.index[self.data[FILE_NAME] == item + ".xml"]
                if not index.empty:
                    self.data.drop(index, axis=0, inplace=True)
                    pwarn("Item {0} from errors.csv was deleted.".format(item))
        else:
            perr(
                '\nA file called "errors.csv" must be created containing Filenames to be deleted.'
            )

    def delete_undesired_columns(self, **kwargs) -> None:
        """Deletes not necessary columns for statistical analysis.

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
        config_data = self._post_config.to_dict_post()
        config_data.update(kwargs)  # Override values
        try:
            delete_columns(self.data, config_data)
        except KeyError:
            perr("Some columns are already not present in the Dataframe")

    def replace_nans(self) -> None:
        for col in tqdm(
            self.data.columns, desc="Replacing NaN values in selected columns"
        ):
            if any(
                substring in col for substring in tuple(self._post_config.replace_nans)
            ):
                self.data[col] = self.data[col].fillna(0)

    def save(self, dest_path: Union[str, PurePath], ft="csv") -> None:
        """Saves current information into a file given the name of dest_path

        To load one of those file, remember to set the index to `AriaId`, and, if
        windows are used, to `WindowId`:

        ```python
        df = pd.read_csv('window_alldata.csv').set_index(['AriaId', 'WindowId'])
        ```

        Parameters
        ----------
        dest_path : str or Path
            Path to directory where the file will be stored; a suffix like
            `_metadata.csv` will be added.
        ft : str
            Type of file for saving. The filetype must be supported by `pandas`, e.g.
            `to_csv`, `to_feather`, `to_parquet`, etc.
        """

        pinfo(f"Written data to {dest_path}_*.csv")
        ft = "to_" + ft
        dest_path = str(dest_path)
        getattr(self.label_dataframe, ft)(dest_path + "_labels.csv", index=False)
        getattr(self.metadata_dataframe, ft)(dest_path + "_metadata.csv", index=False)
        getattr(self.features_dataframe, ft)(dest_path + "_features.csv", index=False)
        getattr(self.data, ft)(dest_path + "_alldata.csv", index=False)

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
            i for i in self.data.columns if "_Degree" in i and not "relative" in i
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

        self.data = self._check_columns_type(self.data)
        self.data = self.data.reindex(sorted(self.data.columns), axis=1)
        self.data.drop("index", axis=1, inplace=True, errors="ignore")

        self._split_metadata_and_labels()

        if hasattr(self, "destination_route"):
            dest_path = self.destination_route + "_features"
            self.save(dest_path)

    def _split_metadata_and_labels(self) -> None:
        label_columns = list(self.data.filter(like="Label_", axis=1))

        self.label_dataframe = self.data[[ID, WINDOW_ID] + label_columns]
        self.metadata_dataframe = self.data[[ID, WINDOW_ID] + metadata_columns]
        self.data = sort_columns(self.data, [ID, WINDOW_ID] + priority_columns)

        self.features_dataframe = self.data.drop(
            priority_columns + label_columns, axis=1, errors="ignore"
        )

    def _check_columns_type(self, df) -> DataFrame:
        for column in tqdm(df.columns, desc="Adjusting NaN values"):
            column_type = Counter(df[df[column].notna()][column].map(type)).most_common(
                1
            )[0][0]
            if column_type == str:
                df[column] = df[column].replace(0, "0")
                df[column] = df[column].fillna(str("NA"))

            else:
                df[column] = df[column].fillna(float("NaN"))
                df[column] = df[column].replace("0", 0)
        return df
