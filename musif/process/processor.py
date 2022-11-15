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
from musif.extract.basic_modules.file_name.constants import ARIA_ID, ARIA_LABEL
from musif.extract.basic_modules.scoring.constants import (INSTRUMENTATION,
                                                           ROLE_TYPE, SCORING,
                                                           VOICES)
from musif.extract.features.composer.handler import COMPOSER
from musif.extract.features.core.constants import FILE_NAME
from musif.extract.features.harmony.constants import (HARMONY_AVAILABLE,
                                                      KEY_MODULATORY,
                                                      KEY_PREFIX,
                                                      CHORDS_GROUPING_prefix)
from musif.extract.features.prefix import get_part_prefix, get_sound_prefix
from musif.logs import perr, pinfo, pwarn
from musif.process.constants import (PRESENCE, label_by_col, metadata_columns,
                                     priority_columns, voices_list_prefixes)
from musif.process.utils import (_join_double_bass, delete_columns, join_keys,
                                 join_keys_modulatory, join_part_degrees,
                                 log_errors_and_shape, merge_duetos_trios,
                                 merge_single_voices, split_passion_A)


# TODO: documentation should be more precise here and there, reread
class DataProcessor:
    """Processor class that treats columns and information of a DataFrame

    This operator processes information from a DataFrame or a .csv file. 
    It deletes unseful columns and merges those that are required to clean the data.
    The main method .process() returns a DataFrame and saves it into a .csv file.
    Requires to have a Passions.csv file in the current working directory containing each passion
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
        Processes all the DataFrame information and saves it to a .csv file
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
    delete_unwanted_columns(**kwargs)
        Deletes all columns that are not needed according to config.yml file  
    to_csv(dest_path: str)
        Saves final information to a csv file 
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
            Dataframe with the information from either the file or the previous DataFrame.
        """

        try:
            if isinstance(info, str) or isinstance(info, PurePath):
                pinfo('\nReading csv file...')
                if not os.path.exists(info):
                    raise FileNotFoundError('A .csv file could not be found')
                if isinstance(info, PurePath):
                    self.destination_route = str(info.with_suffix(''))
                else:
                    self.destination_route = info.replace('.csv', '')
                df = pd.read_csv(info, low_memory=False,
                                 sep=',', encoding_errors='replace')
                if df.empty:
                    raise FileNotFoundError(
                        'The .csv file could not be found.')
                return df

            elif isinstance(info, DataFrame):
                pinfo('\nProcessing DataFrame...')
                return info
            else:
                perr(
                    'Wrong info type! You must introduce either a DataFrame either the name of a .csv file.')
                return pd.DataFrame()

        except OSError as e:
            perr(
                f'Data could not be loaded. Either wrong path or an empty file was found. {e}')
            return e

    def process(self) -> DataFrame:
        """
        Main method tof the class. Removes NaN values, deletes unuseful columns
        and merges those that are needed according to config.yml file. Saves processed DataFrame 
        into a csv file.

        Returns
        ------
        Dataframe object        
        """
        if FILE_NAME in self.data:
            self.data[FILE_NAME].to_csv(
                self._post_config.check_file, index=False)

        if self._post_config.delete_files:
            self.delete_previous_items()

        pinfo('\nPreprocessing data...')
        self.preprocess_data()
        pinfo('\nScanning info looking for missing data...')
        self._scan_dataframe()

        if self._post_config.unbundle_instrumentation:
            pinfo('\nSeparating "Instrumentation" column...')
            self.unbundle_instrumentation()

        if self._post_config.merge_voices:
            self.merge_voices()

        self.delete_unwanted_columns()

        if self._post_config.grouped_analysis:
            self.group_columns()

        self._final_data_processing()
        return self.data

    def assign_labels(self) -> None:
        """Crosses passions labels from Passions.csv file with the DataFrame so every row (aria)
        gets assigned to its own Label
        """
        passions = read_dicts_from_csv(os.path.join(
            self.internal_data_dir, "Passions.csv"))

        data_by_aria_label = {label_data["Label"]                              : label_data for label_data in passions}
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
        """ Adds labels to arias. Cleans data and removes columns with no information or rows without assigned Label
        """
        self.assign_labels()
        if 'Label_Passions' in self.data:
            del self.data['Label_Passions']
        if 'Label_Sentiment' in self.data:
            del self.data['Label_Sentiment']

        print('Deleted arias without passion: ',
              self.data[self.data["Label_BasicPassion"].isnull()].shape[0])
        self.data = self.data[~self.data["Label_BasicPassion"].isnull()]

        self.data.dropna(axis=1, how='all', inplace=True)
        self.data.reset_index(inplace=True, drop=True)

    def group_columns(self) -> None:
        """Groups Key_*_PercentageMeasures, Key_Modulatory and Degrees columns. Into bigger groups
        for agregated analysis, keeping the previous ones. Also deletes unnecesary columns for analysis.
        """

        # self.data.drop([i for i in self.data.columns if 'Degree' in i and not '_relative' in i], axis = 1, inplace=True)
        # self.data.drop([i for i in self.data.columns if i.startswith(CHORDS_GROUPING_prefix+'1')], axis = 1, inplace=True)
        try:
            self._group_keys_modulatory()
            self._group_keys()
            self._join_degrees()
            self._join_degrees_relative()
        except KeyError:
            perr('Some columns to group could not be found.')

    def merge_voices(self) -> None:
        """Finds multiple singers arias (duetos/trietos) and calculates mean, max or min between them.
        Unifies all voices columns into SoundVoice_ columns. 
        Also collapses PartBsI and PartBsII in one column.
        """
        pinfo('\nScaning voice columns')
        df_voices = self.data[[col for col in self.data.columns if any(
            substring in col for substring in voices_list_prefixes)]]
        self.data[df_voices.columns] = self.data[df_voices.columns].replace(
            'NA', np.nan)

        merge_single_voices(self.data)
        self.data = merge_duetos_trios(self.data)

        columns_to_delete = [i for i in self.data.columns.values if any(
            voice in i for voice in voices_list_prefixes)]
        self.data.drop(columns_to_delete, axis=1, inplace=True)

        self.data = _join_double_bass(self.data)

    def unbundle_instrumentation(self) -> None:
        """Separates Instrumentation column into as many columns as instruments present in Instrumentation,
        assigning 1 for every instrument that is present and 0 if it is not for every row (aria).
        """

        for i, row in enumerate(self.data[INSTRUMENTATION]):
            for element in row.split(','):
                self.data.at[i, PRESENCE+'_' + element] = 1

        self.data[[i for i in self.data if PRESENCE+'_' in i]] = self.data[[
            i for i in self.data if PRESENCE+'_' in i]].fillna(0).astype(int)

    def delete_previous_items(self) -> None:
        """Deletes items from 'errors.csv' file in case they were not extracted properly"""
        pinfo('\nDeleting items with errors...')
        errors_file=r'./errors.csv'
        if os.path.exists(errors_file):
            errors = pd.read_csv(errors_file, low_memory=False,
                                 encoding_errors='replace', header=0)[FILE_NAME].tolist()
            for item in errors:
                index = self.data.index[self.data[FILE_NAME] == item+'.xml']
                if not index.empty:
                    self.data.drop(index, axis=0, inplace=True)
                    pwarn('Item {0} from errors.csv was deleted.'.format(item))
        else:
            perr(
                '\nA file called "errors.csv" must be created containing Filenames to be deleted.')

    def delete_unwanted_columns(self, **kwargs) -> None:
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
            perr('Some columns are already not present in the Dataframe')

    def replace_nans(self) -> None:
        for col in tqdm(self.data.columns, desc='Replacing NaN values in selected columns'):
            if any(substring in col for substring in tuple(self._post_config.replace_nans)):
                self.data[col] = self.data[col].fillna(0)

    def to_csv(self, dest_path: str, df: DataFrame) -> None:
        """Saves current information into a .csv file given the name onf dest_path

        Parameters
        ----------
        dest_path : str
            Path to the route where the .csv file needs to be stored.
        """
        dest_path = dest_path + '.csv'
        df.to_csv(dest_path, index=False)
        pinfo(f'\nData succesfully saved as {dest_path} in current directory.')

    def _group_keys_modulatory(self) -> None:
        self.data.update(
            self.data[[i for i in self.data.columns if KEY_PREFIX+KEY_MODULATORY in i]].fillna(0))
        join_keys_modulatory(self.data)

    def _group_keys(self) -> None:
        self.data.update(
            self.data[[i for i in self.data.columns if KEY_PREFIX in i]].fillna(0))
        join_keys(self.data)

    def _join_degrees(self) -> None:
        total_degrees = [
            i for i in self.data.columns if '_Degree' in i and not 'relative' in i]

        for part in self._post_config.instruments_to_keep:
            join_part_degrees(total_degrees, get_part_prefix(part), self.data)
        join_part_degrees(total_degrees, get_sound_prefix('voice'), self.data)
        # self.data.drop(total_degrees, axis = 1, inplace=True)

    def _join_degrees_relative(self) -> None:
        total_degrees = [
            i for i in self.data.columns if '_Degree' in i and 'relative' in i]

        for part in self._post_config.instruments_to_keep:
            join_part_degrees(total_degrees, get_part_prefix(
                part), self.data, sufix='_relative')
        join_part_degrees(total_degrees, get_sound_prefix(
            'voice'), self.data,  sufix='_relative')
        # self.data.drop(total_degrees, axis = 1, inplace=True)

    def _scan_dataframe(self):
        self.composer_counter = []
        self.novoices_counter = []
        self._scan_composers()
        self._scan_voices()
        if self._post_config.delete_files_without_harmony:
            if HARMONY_AVAILABLE in self.data:
                number_files = len(
                    self.data[self.data[HARMONY_AVAILABLE] == 0])
                pinfo(
                    f"{number_files} files were found without mscx analysis or errors in harmonic analysis. They'll be deleted.")
                pinfo(
                    f'{self.data[self.data[HARMONY_AVAILABLE] == 0][FILE_NAME].to_string()}')
                # self.data = self.data[self.data[HARMONY_AVAILABLE] != 0]

    def _scan_voices(self):
        for i, voice in enumerate(self.data[VOICES].values):
            if pd.isnull(voice):
                self.novoices_counter.append(self.data[FILE_NAME][i])
                self.data.drop(i, axis=0, inplace=True)

    def _scan_composers(self):
        composers_path = os.path.join(self.internal_data_dir, 'composers.csv')

        if os.path.exists(composers_path):
            composers = pd.read_csv(composers_path)
            composers = [i for i in composers.iloc[:, 0].to_list()
                         if str(i) != 'nan']

            for i, comp in enumerate(self.data[COMPOSER].values):
                if pd.isnull(comp):
                    self.composer_counter.append(self.data[FILE_NAME][i])
                    self.data.drop(i, axis=0, inplace=True)
                elif comp.strip() not in composers:
                    aria_name = self.data.at[i, FILE_NAME]
                    correction = difflib.get_close_matches(comp, composers)
                    correction = correction[0] if correction else 'NA'
                    self.data.at[i, COMPOSER] = correction
                    pwarn(
                        f'Composer {comp} in aria {aria_name} was not found. Replaced with: {correction}')
                    if correction == 'NA':
                        self.composer_counter.append(self.data[FILE_NAME][i])
                        self.data.drop(i, axis=0, inplace=True)  # ?

        else:
            perr('Composers file could not be found.')

    def _final_data_processing(self) -> None:
        self.data.sort_values(ARIA_ID, inplace=True)
        self.replace_nans()

        self.data = self._check_columns_type(self.data)
        self.data = self.data.reindex(sorted(self.data.columns), axis=1)
        self.data.drop('index', axis=1, inplace=True, errors='ignore')

        log_errors_and_shape(self.composer_counter,
                             self.novoices_counter, self.data)
        self._split_metadata_and_labels()

        dest_path = self.destination_route + "_features"
        self.to_csv(dest_path, self.data)

    def _split_metadata_and_labels(self) -> None:
        self.data.rename(columns={ROLE_TYPE: 'Label_'+ROLE_TYPE}, inplace=True)
        label_columns = list(self.data.filter(like='Label_', axis=1))

        label_dataframe = self.data[[ARIA_ID] + label_columns]

        metadata_dataframe = self.data[[ARIA_ID] + metadata_columns]

        self.to_csv(self.destination_route + "_labels", label_dataframe)
        self.to_csv(self.destination_route + "_metadata", metadata_dataframe)
        #TODO: donde estan key y key signature
        self.data = sort_columns(self.data, [ARIA_ID] + priority_columns)
        self.to_csv(self.destination_route + "_alldata", self.data)

        self.data.drop(priority_columns + label_columns,
                       inplace=True, axis=1, errors='ignore')

    def _check_columns_type(self, df) -> DataFrame:
        for column in tqdm(df.columns, desc='Adjusting NaN values'):
            column_type = Counter(
                df[df[column].notna()][column].map(type)).most_common(1)[0][0]
            if column_type == str:
                df[column] = df[column].replace(0, '0')
                df[column] = df[column].fillna(str("NA"))
                # df[column]= df[column].replace(np.nan, str("NA"))

            else:
                df[column] = df[column].fillna(float("NaN"))
                df[column] = df[column].replace('0', 0)
        return df
