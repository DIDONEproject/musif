import difflib
import os
from collections import Counter
from pathlib import Path, PurePath
from typing import Union

import numpy as np
import pandas as pd
from pandas import DataFrame
from tqdm import tqdm

from musif.common._utils import read_dicts_from_csv
from musif.common.sort import sort_columns
from musif.config import PostProcess_Configuration
from musif.extract.constants import WINDOW_ID
from musif.extract.basic_modules.file_name.constants import ARIA_ID, ARIA_LABEL
from musif.extract.basic_modules.scoring.constants import (
    INSTRUMENTATION,
    ROLE_TYPE,
    SCORING,
    VOICES,
)
from musif.extract.basic_modules.composer.handler import COMPOSER
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
    voices_list_prefixes,
)
from musif.process.processor_general import DataProcessor
from musif.process.utils import (
    _join_double_bass,
    delete_columns,
    join_keys,
    join_keys_modulatory,
    join_part_degrees,
    log_errors_and_shape,
    merge_duetos_trios,
    merge_single_voices,
    split_passion_A,
)


class DataProcessorDidone(DataProcessor):
    """Processor class that treats columns and information of a DataFrame

    This operator processes information from a DataFrame or a .csv file. 
    It deletes unseful columns for analysis and saves important ones. For duetos and trios, it
    merges the merges the singer columns in the same one with the proper calculations.
    Also saves data in several files in .csv format.
    The main method .process() returns a DataFrame and saves data.
    Requires to have a Passions.csv file in ./internal_data directory containing each passion
    for each aria.
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
        Assigns labels from file Passion.csv to DataFrame according to AriaLabel column
    preprocess_data()
        Deletes columns with no information, convertes 0 to nan and depurates data
    group_columns()
        Groups thos columns related to Keys, Key_Modulatory and Degree for agregated analysis
    merge_voices()
        Joins every voice part into common columns startung with 'SoundVoice'. Also fixes duetos.
    unbundle_instrumentation()
        Separates 'Instrumentation' column into several Presence_ columns for every instrument present in Instrumentation.
    delete_undesired_columns(**kwargs)
        Deletes all columns that are not needed according to config.yml file  
    save(dest_path: str)
        Saves final information to various csv files, splitting data, metadata and
        features
    """
    

    def process(self) -> DataFrame:
        """
        Main method of the class. Removes NaN values, deletes unuseful columns
        and merges those that are needed according to config.yml file.
        Saves processed DataFrame into a csv file if the input was a path to a file.

        Returns
        ------
        Dataframe object
        """
        if FILE_NAME in self.data:
            self.data[FILE_NAME].to_csv(self._post_config.check_file, index=False)

        if self._post_config.delete_files:
            self.delete_previous_items()

        pinfo("\nPreprocessing data...")
        self.preprocess_data()
        pinfo("\nScanning info looking for missing data...")
        self._scan_dataframe()

        if self._post_config.unbundle_instrumentation:
            pinfo('\nSeparating "Instrumentation" column...')
            self.unbundle_instrumentation()

        if self._post_config.merge_voices:
            self.merge_voices()

        self.delete_undesired_columns()

        if self._post_config.grouped_analysis:
            self.group_columns()

        self._final_data_processing()
        return self.data

    def assign_labels(self) -> None:
        """Crosses passions labels from Passions.csv file with the DataFrame so every row (aria)
        gets assigned to its own Label
        """
        passions = read_dicts_from_csv(
            os.path.join(self.internal_data_dir, "Passions.csv")
        )

        data_by_aria_label = {
            label_data["Label"]: label_data for label_data in passions
        }
        for col, label in label_by_col.items():
            values = []
            for _, row in self.data.iterrows():
                data_by_aria = data_by_aria_label.get(row[ARIA_LABEL])
                label_value = data_by_aria[col] if data_by_aria else None
                values.append(label_value)
            self.data[label] = values

        if self._post_config.split_passionA:
            split_passion_A(self.data)

    def preprocess_data(self) -> None:
        """Adds labels to arias. Cleans data and removes columns with no information or rows without assigned Label"""
        self.assign_labels()
        if "Label_Passions" in self.data:
            del self.data["Label_Passions"]
        if "Label_Sentiment" in self.data:
            del self.data["Label_Sentiment"]

        print(
            "Deleted arias without passion: ",
            self.data[self.data["Label_BasicPassion"].isnull()].shape[0],
        )
        self.data = self.data[~self.data["Label_BasicPassion"].isnull()]

        self.data.dropna(axis=1, how="all", inplace=True)

    def merge_voices(self) -> None:
        """Finds multiple singers arias (duetos/trietos) and calculates mean, max or min between them.
        Unifies all voices columns into SoundVoice_ columns.
        Also collapses PartBsI and PartBsII in one column.
        """
        pinfo("\nScaning voice columns")
        df_voices = self.data[
            [
                col
                for col in self.data.columns
                if any(substring in col for substring in voices_list_prefixes)
            ]
        ]
        self.data[df_voices.columns] = self.data[df_voices.columns].replace(
            "NA", np.nan
        )

        merge_single_voices(self.data)
        self.data = merge_duetos_trios(self.data)

        columns_to_delete = [
            i
            for i in self.data.columns.values
            if any(voice in i for voice in voices_list_prefixes)
        ]
        self.data.drop(columns_to_delete, axis=1, inplace=True)

        self.data = _join_double_bass(self.data)

    def delete_previous_items(self) -> None:
        """Deletes items from 'errors.csv' file in case they were not extracted properly"""
        pinfo("\nDeleting items with errors...")
        errors_file = r"./errors.csv"
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

    def _scan_dataframe(self):
        self.composer_counter = []
        self.novoices_counter = []
        self._scan_composers()
        self._scan_voices()
        if self._post_config.delete_files_without_harmony:
            self.delete_files_without_harmony()

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

    def _scan_voices(self):
        for i, voice in enumerate(self.data[VOICES].values):
            if pd.isnull(voice):
                self.novoices_counter.append(self.data[FILE_NAME][i])
                self.data.drop(i, axis=0, inplace=True)

    def _scan_composers(self):
        composers_path = os.path.join(self.internal_data_dir, "composers.csv")

        if os.path.exists(composers_path):
            composers = pd.read_csv(composers_path)
            composers = [i for i in composers.iloc[:, 0].to_list() if str(i) != "nan"]

            for i, comp in enumerate(self.data[COMPOSER].values):
                if pd.isnull(comp):
                    self.composer_counter.append(self.data[FILE_NAME][i])
                    self.data.drop(i, axis=0, inplace=True)
                elif comp.strip() not in composers:
                    aria_name = self.data.at[i, FILE_NAME]
                    correction = difflib.get_close_matches(comp, composers)
                    correction = correction[0] if correction else "NA"
                    self.data.at[i, COMPOSER] = correction
                    pwarn(
                        f"Composer {comp} in aria {aria_name} was not found. Replaced with: {correction}"
                    )
                    if correction == "NA":
                        self.composer_counter.append(self.data[FILE_NAME][i])
                        self.data.drop(i, axis=0, inplace=True)  # ?

        else:
            perr("Composers file could not be found.")

    def _final_data_processing(self) -> None:
        self.data.sort_values([ARIA_ID, WINDOW_ID], inplace=True)
        self.replace_nans()

        self.data = self._check_columns_type(self.data)
        self.data = self.data.reindex(sorted(self.data.columns), axis=1)
        self.data.drop("index", axis=1, inplace=True, errors="ignore")

        log_errors_and_shape(self.composer_counter, self.novoices_counter, self.data)

        self._split_metadata_and_labels()

        if hasattr(self, "destination_route"):
            dest_path = self.destination_route + "_features"
            self.save(dest_path)

    def _split_metadata_and_labels(self) -> None:
        self.data.rename(columns={ROLE_TYPE: "Label_" + ROLE_TYPE}, inplace=True)
        label_columns = list(self.data.filter(like="Label_", axis=1))

        self.label_dataframe = self.data[[ARIA_ID, WINDOW_ID] + label_columns]

        self.metadata_dataframe = self.data[[ARIA_ID, WINDOW_ID] + metadata_columns]

        # TODO: donde estan key y key signature
        self.data = sort_columns(self.data, [ARIA_ID, WINDOW_ID] + priority_columns)

        self.features_dataframe = self.data.drop(
            priority_columns + label_columns, axis=1, errors="ignore"
        )