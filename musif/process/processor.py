import sys
from typing import Optional, Union

import pandas as pd
from musif.config import PostProcess_Configuration
from musif.process.utils import (delete_columns, delete_previous_items,
                                 join_keys, join_keys_modulatory,
                                 join_part_degrees, log_errors_and_shape,
                                 merge_duetos_trios, merge_single_voices,
                                 replace_nans)
from pandas import DataFrame

sys.path.insert(0, "../musif")
import os

import numpy as np
from musif.common.sort import sort_columns
from musif.common.utils import read_dicts_from_csv
from musif.extract.features.composer.handler import COMPOSER
from musif.extract.features.core.constants import FILE_NAME
from musif.extract.features.file_name.constants import ARIA_ID, ARIA_LABEL
from musif.extract.features.harmony.constants import (KEY_MODULATORY,
                                                      CHORDS_GROUPING_prefix,
                                                      KEY_prefix)
from musif.extract.features.prefix import get_part_prefix, get_sound_prefix
from musif.extract.features.scoring.constants import INSTRUMENTATION, VOICES
from musif.logs import perr, pinfo

from .constants import (PRESENCE, columns_order, label_by_col,
                        voices_list_prefixes)


class DataProcessor:
    """
    Processes a corpus given a directory with xml and mscx files and saves
    the obtained DataFrame into a .csv file. It deletes unseful columns and merges those that are needed
    to prepare the DataFrame for later analysis
    """
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args:  Could be a path to a .yml file, a Configuration object or a dictionary. Length zero or one.
        **kwargs: Get keywords to construct Configuration.
        """

        self._post_config=PostProcess_Configuration(*args, **kwargs)
        self.info=kwargs.get('info')
        self.data = self.process_info(self.info)

    def process_info(self, info: Union[str, DataFrame] ) -> DataFrame:
        """
        Extracts features given in the configuration data getting a file, directory or several files paths,
        returning a DataFrame of the score.

        Returns
        ------
            Score dataframe with the extracted features of given scores.
        """
        
        if isinstance(info, str):
            pinfo('\nReading csv file...')
            if not os.path.exists(info):
                perr("The .csv file doesn't exists!")
                return pd.DataFrame()
            self.destination_route=info.replace('.csv','')
            df = pd.read_csv(info, low_memory=False, sep=',', encoding_errors='replace')
            df[FILE_NAME].to_csv(self._post_config.check_file, index=False)
            return df
        
        elif isinstance(info, DataFrame):
            pinfo('\nProcessing DataFrame...')
            return df
        else:
            perr('Wrong info type! You must introduce either a DataFrame either the name of a .csv file.')

    def process(self) -> DataFrame:
        if self._post_config.delete_files:
            delete_previous_items()
        
        self._assign_labels()
        pinfo('\nPreprocessing data...')
        self.preprocess_data()

        if self._post_config.unbundle_instrumentation:
            pinfo('\nSeparating "Instrumentation" column...')
            self.unbundle_instrumentation()

        pinfo('\nScanning info looking for errors...')
        self._scan_dataframe()
        
        if self._post_config.merge_voices:
            self.merge_voices()
        pinfo('\nDeleting not useful columns...')
        self.delete_unwanted_columns()

        if self._post_config.grouped_analysis:
            self.group_columns()

        self._final_data_processing()            
        return self.data

    def group_columns(self) -> None:
        self.data.drop([i for i in self.data.columns if 'Degree' in i and not '_relative' in i], axis = 1, inplace=True)
        self.data.drop([i for i in self.data.columns if i.startswith(CHORDS_GROUPING_prefix+'1')], axis = 1, inplace=True)
        self.group_keys_modulatory()
        self.group_keys()
        self.join_degrees()

    def group_keys_modulatory(self) -> None:
        self.data.update(self.data[[i for i in self.data.columns if KEY_prefix+KEY_MODULATORY in i]].fillna(0))
        join_keys_modulatory(self.data)

    def group_keys(self) -> None:
        self.data.update(self.data[[i for i in self.data.columns if KEY_prefix in i]].fillna(0))
        join_keys(self.data)

    def join_degrees(self) -> None:
        total_degrees = [i for i in self.data.columns if '_Degree' in i]

        for part in self._post_config.instruments_to_keep:
            join_part_degrees(total_degrees, get_part_prefix(part), self.data)
        join_part_degrees(total_degrees, get_sound_prefix('voice'), self.data)
        # self.data.drop(total_degrees, axis = 1, inplace=True)
    
    def merge_voices(self) -> None:
        pinfo('\nScaning voice columns...')
        generic_sound_voice_prefix = get_sound_prefix('Voice') 
        # Delete columns that contain strings 
        df_voices=self.data[[col for col in self.data.columns if any(substring in col for substring in voices_list_prefixes)]]
        cols_to_delete=df_voices.select_dtypes(include=['object']).columns
        self.data.drop(cols_to_delete, axis = 1, inplace=True)
        merge_duetos_trios(self.data, generic_sound_voice_prefix)
        merge_single_voices(self.data, generic_sound_voice_prefix)

    def preprocess_data(self) -> None:
        if 'Label_Passions' in self.data:
            del self.data['Label_Passions']
        if 'Label_Sentiment' in self.data:
            del self.data['Label_Sentiment']

        self.data = self.data[~self.data["Label_BasicPassion"].isnull()]
        self.data.replace(0.0, np.nan, inplace=True)
        self.data.dropna(axis=1, how='all', inplace=True)
        self.data.reset_index(inplace=True)

    def unbundle_instrumentation(self) -> None:
        for i, row in enumerate(self.data[INSTRUMENTATION]):
            for element in row.split(','):
                self.data.at[i, PRESENCE+'_'+element] = 1

    def delete_unwanted_columns(self) -> None:
        try:
            delete_columns(self.data, self._post_config)
        except KeyError:
            perr('Some columns are already not present in the Dataframe')
    
    def _assign_labels(self) -> None:
        passions = read_dicts_from_csv("Passions.csv")
        data_by_aria_label = {label_data["Label"]: label_data for label_data in passions}
        for col, label in label_by_col.items():
            values = []
            for _, row in self.data.iterrows():
                data_by_aria = data_by_aria_label.get(row[ARIA_LABEL])
                label_value = data_by_aria[col] if data_by_aria else None
                values.append(label_value)
            self.data[label] = values

        if self._post_config.split_passionA:
            self.split_passion_A(self.data)
  

    def _scan_dataframe(self):
        self.composer_counter = []
        self.novoices_counter = []

        for i, comp in enumerate(self.data[COMPOSER].values):
            if pd.isnull(comp):
                self.composer_counter.append(self.data[FILE_NAME][i])
                self.data.drop(i, axis = 0, inplace=True)

        for i, voice in enumerate(self.data[VOICES].values):
            if pd.isnull(voice):
                self.novoices_counter.append(self.data[FILE_NAME][i])
                self.data.drop(i, axis = 0, inplace=True)

    def _final_data_processing(self) -> None:
        self.data.sort_values(ARIA_ID, inplace=True)
        replace_nans(self.data)
        log_errors_and_shape(self.composer_counter, self.novoices_counter, self.data)
        self.data = self.data.reindex(sorted(self.data.columns), axis=1)
        self.data = sort_columns(self.data, columns_order)
        dest_path=self.destination_route + "_processed" + ".csv"
        self.data.to_csv(dest_path, index=False)
        pinfo(f'\nData saved as {dest_path}')

