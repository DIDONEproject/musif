import sys
from typing import List, Optional, Union

import pandas as pd
from tqdm import tqdm
from build.lib.musif.extract.features.dynamics.constants import DYNABRUPTNESS
from musif.config import PostProcess_Configuration
from musif.extract.features.ambitus.constants import HIGHEST_NOTE, HIGHEST_NOTE_INDEX, LOWEST_NOTE, LOWEST_NOTE_INDEX
from musif.extract.features.interval.constants import LARGEST_INTERVAL_ALL
from musif.process.utils import (delete_previous_items, join_keys,
                                 join_keys_modulatory, join_part_degrees,
                                 log_errors_and_shape, merge_duetos_trios, merge_single_voices,
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
                                                      KEY_PERCENTAGE,
                                                      CHORDS_GROUPING_prefix,
                                                      KEY_prefix)
from musif.extract.features.prefix import get_part_prefix, get_sound_prefix
from musif.extract.features.scoring.constants import (FAMILY_INSTRUMENTATION,
                                                      FAMILY_SCORING,
                                                      INSTRUMENTATION,
                                                      NUMBER_OF_PARTS, SCORING,
                                                      VOICES)
from musif.extract.features.tempo.constants import NUMBER_OF_BEATS
from musif.extract.features.texture.constants import TEXTURE
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
    

    def process_corpora(self, info: Union[str, pd.DataFrame]) -> DataFrame:
        
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
            df = self.process_dataframe(df)
            return df
        
        elif isinstance(info, DataFrame):
            pinfo('\nProcessing DataFrame...')
            df = self.process_dataframe(info)
            return df
        else:
            perr('Wrong info type! You must introduce either a DataFrame either the name of a .csv file.')


    def process_dataframe(self, df: str) -> DataFrame:
        if self._post_config.delete_files:
            delete_previous_items(df)
        
        self._assign_labels(df)

        pinfo('\nPreprocessing data...')
        self.preprocess_data(df)

        if self._post_config.unbundle_instrumentation:
            pinfo('\nSeparating "Instrumentation" column...')
            self.unbundle_instrumentation(df)


        pinfo('\nScanning info looking for errors...')
        composer_counter, novoices_counter = self._scan_dataframe(df)
        
        pinfo('\nMerging voice columns...')
        if self._post_config.merge_voices:
            self.merge_voices(df)
        pinfo('\nDeleting not useful columns...')
        self.delete_unwanted_columns(df)

        if self._post_config.grouped_analysis:
            df.drop([i for i in df.columns if 'Degree' in i and not '_relative' in i], axis = 1, inplace=True)
            df.drop([i for i in df.columns if i.startswith(CHORDS_GROUPING_prefix+'1')], axis = 1, inplace=True)

            self.group_keys_modulatory(df)
            self.group_keys(df)
            self.join_degrees(df)

        self._final_data_processing(columns_order, composer_counter, novoices_counter, df)            
        return df
    @staticmethod
    def group_keys_modulatory(df: DataFrame) -> None:
        df.update(df[[i for i in df.columns if KEY_prefix+KEY_MODULATORY in i]].fillna(0))
        join_keys_modulatory(df)
    @staticmethod
    def group_keys(df: DataFrame) -> None:
        df.update(df[[i for i in df.columns if KEY_prefix in i]].fillna(0))
        join_keys(df)

    def join_degrees(self, df: DataFrame) -> None:
        total_degrees = [i for i in df.columns if '_Degree' in i]

        for part in self._post_config.instruments_to_keep:
            join_part_degrees(total_degrees, get_part_prefix(part), df)

        join_part_degrees(total_degrees, get_sound_prefix('voice'), df)
        # df.drop(total_degrees, axis = 1, inplace=True)
    
    @staticmethod
    def merge_voices(df: DataFrame) -> None:
        generic_sound_voice_prefix = get_sound_prefix('Voice')
        # Delete columns that contain strings 
        df_voices=df[[col for col in df.columns if any(substring in col for substring in voices_list_prefixes)]]
        cols_to_delete=df_voices.select_dtypes(include=['object']).columns
        df.drop(cols_to_delete, axis = 1, inplace=True)
        merge_duetos_trios(df, generic_sound_voice_prefix)
        merge_single_voices(df, generic_sound_voice_prefix)

    @staticmethod
    def preprocess_data(df: DataFrame) -> None:
        if 'Label_Passions' in df:
            del df['Label_Passions']

        if 'Label_Sentiment' in df:
            del df['Label_Sentiment']

        df = df[~df["Label_BasicPassion"].isnull()]
        df.replace(0.0, np.nan, inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        df.reset_index(inplace=True)

    @staticmethod
    def unbundle_instrumentation(df) -> None:
        for i, row in enumerate(df[INSTRUMENTATION]):
            for element in row.split(','):
                df.at[i, PRESENCE+'_'+element] = 1

    def delete_unwanted_columns(self, df):
        #METHODS TO IMPROVE
        # df.columns[df.columns.str.endswith((HIGHEST_NOTE, LOWEST_NOTE))]
        # df.filter(like='Label').columns

        for inst in self._post_config.instruments_to_kill:
            df.drop([i for i in df.columns if 'Part'+inst in i], axis = 1, inplace=True)
        
        for inst in self._post_config.presence_to_kill:
            df.drop([i for i in df.columns if inst in i], axis = 1, inplace=True)

        df.drop([i for i in df.columns if get_part_prefix('Vn') in i], axis = 1, inplace=True)

        # Delete other unuseful columns
        # df.drop([i for i in df.columns if i.startswith('HighestNote') or i.startswith('LowestNote')], axis = 1, inplace=True)
        columns_to_remove = tuple(['_Count'])
        columns_endswith=(HIGHEST_NOTE, LOWEST_NOTE, '_Notes', '_SoundingMeasures', '_Syllables', '_NumberOfFilteredParts', 
        NUMBER_OF_PARTS, '_NotesMean', 'Librettist', '_LargestIntervalAsc', '_LargestIntervalAll','_LargestIntervalDesc', '_NotesMean',
        'Semitones_Sum', '_MeanInterval')
        df.drop([i for i in df.columns if i.endswith(columns_endswith)], axis = 1, inplace=True)
        df.drop([i for i in df.columns if '_Count' in i], axis = 1, inplace=True)
        df.drop([i for i in df.columns if i.startswith(('FamilyWw', 'FamilyBr', 'EndOfThemeA', NUMBER_OF_BEATS, 'SoundVoice_Dyn'))], axis = 1, inplace=True)


        if (FAMILY_INSTRUMENTATION and FAMILY_SCORING) in df:
            df.drop([FAMILY_INSTRUMENTATION, FAMILY_SCORING], axis = 1, inplace=True)

        cols_to_remove=('_SoundingMeasuresMean', '_SmallestSemitones', '_SmallestAbsolute', '_SmallestInterval')
        df.drop([col for col in df.columns if any(substring in col for substring in cols_to_remove)], axis = 1, inplace=True)
        
        cols_to_remove=['Presence_of_bs', 'Presence_of_va', 'Presence_of_vc', 'Presence_of_vn']
        df.drop(cols_to_remove, axis = 1, inplace=True)
        
        df.drop([i for i in df.columns if 'Sound' in i and not 'Voice' in i], axis = 1, inplace=True)
        if 'PartVnI__PartVoice__'+TEXTURE in df:
            del df['PartVnI__PartVoice__'+TEXTURE]

        #remove empty voices
        empty_voices=[col for col in df.columns if col.startswith(tuple(voices_list_prefixes)) and all(df[col].isnull().values)]
        if empty_voices:
            df.drop(empty_voices, axis = 1, inplace=True)

    def _assign_labels(self, df: DataFrame) -> None:
        passions = read_dicts_from_csv("Passions.csv")
        data_by_aria_label = {label_data["Label"]: label_data for label_data in passions}
        for col, label in label_by_col.items():
            values = []
            for _, row in df.iterrows():
                data_by_aria = data_by_aria_label.get(row[ARIA_LABEL])
                label_value = data_by_aria[col] if data_by_aria else None
                values.append(label_value)
            df[label] = values

        if self._post_config.split_passionA:
            df['Label_PassionA_primary']=df['Label_PassionA'].str.split(';', expand=True)[0]
            df['Label_PassionA_secundary']=df['Label_PassionA'].str.split(';', expand=True)[1]
            df['Label_PassionA_secundary'].fillna(df['Label_PassionA_primary'], inplace=True)
            df.drop('Label_PassionA', axis = 1, inplace=True)
    

    def _scan_dataframe(self, df: DataFrame):
        composer_counter = []
        novoices_counter = []

        for i, comp in enumerate(df[COMPOSER].values):
            if pd.isnull(comp):
                composer_counter.append(df[FILE_NAME][i])
                df.drop(i, axis = 0, inplace=True)

        for i, voice in enumerate(df[VOICES].values):
            if pd.isnull(voice):
                novoices_counter.append(df[FILE_NAME][i])
                df.drop(i, axis = 0, inplace=True)

        return composer_counter,novoices_counter

    def _final_data_processing(self, columns_order: List[str], composer_counter: list, novoices_counter: list, df: DataFrame) -> None:
        df.sort_values(ARIA_ID, inplace=True)
        replace_nans(df)
        log_errors_and_shape(composer_counter, novoices_counter, df)
        df = df.reindex(sorted(df.columns), axis=1)
        df = sort_columns(df, columns_order)
        dest_path=self.destination_route + "_processed" + ".csv"
        df.to_csv(dest_path, index=False)
        pinfo(f'\nData saved as {dest_path}')

