import sys
from typing import List

import pandas as pd
from musif.config import Configuration, PostProcess_Configuration
from musif.process.utils import (delete_previous_items, join_part_degrees, log_errors_and_shape,
                                 replace_nans)
from pandas import DataFrame

sys.path.insert(0, "../musif")
import os
import re
import timeit

import numpy as np
from musif.common.sort import sort_columns
from musif.common.utils import read_dicts_from_csv
from musif.extract.extract import FeaturesExtractor, FilesValidator
from musif.extract.features.composer.handler import COMPOSER
from musif.extract.features.core.constants import FILE_NAME
from musif.extract.features.file_name.constants import ARIA_ID, ARIA_LABEL
from musif.extract.features.texture.constants import TEXTURE
from musif.extract.features.harmony.constants import (KEY_MODULATORY,
                                                      KEY_PERCENTAGE,
                                                      CHORDS_GROUPING_prefix,
                                                      KEY_prefix)
from musif.extract.features.prefix import get_part_prefix, get_sound_prefix
from musif.extract.features.scale.constants import DEGREE_PREFIX
from musif.extract.features.scoring.constants import (FAMILY_INSTRUMENTATION,
                                                      FAMILY_SCORING,
                                                      INSTRUMENTATION,
                                                      NUMBER_OF_PARTS, SCORING,
                                                      VOICES)
from musif.extract.features.tempo.constants import NUMBER_OF_BEATS
from musif.logs import ldebug, lerr, linfo, lwarn, pdebug, perr, pinfo, pwarn

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
    

    def process_corpora(self, info: DataFrame) -> DataFrame:
        
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
                return {}
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


    def process_dataframe(self, df: str):
        if self._post_config.delete_files:
            delete_previous_items(df)
        
        self._assign_labels(df)

        pinfo('\nPreprocessing data...')
        self.preprocess_data(df)

        pinfo('\nSeparating "Instrumentation" column...')
        self.unbundle_instrumentation(df)

        pinfo('\nScaning df looking for errors...')
        composer_counter, novoices_counter, duetos_counter = self._scan_dataframe(df)

        pinfo('\nDeleting not useful columns...')
        self.delete_unwanted_columns(df)

        if self._post_config.grouped_analysis:
            df.drop([i for i in df.columns if 'Degree' in i and not '_relative' in i], axis = 1, inplace=True)
            df.drop([i for i in df.columns if i.startswith(CHORDS_GROUPING_prefix+'1')], axis = 1, inplace=True)

            self.group_keys_modulatory(df)
            self.group_keys(df)
            self.join_degrees(df)

        self._final_data_processing(columns_order, composer_counter, novoices_counter, duetos_counter, df)            
        return df
    

    def group_keys_modulatory(self, df: DataFrame):
        df.update(df[[i for i in df.columns if KEY_prefix+KEY_MODULATORY in i]].fillna(0))
        key_SD=[KEY_prefix+KEY_MODULATORY+'IV',KEY_prefix+KEY_MODULATORY+'II', KEY_prefix+KEY_MODULATORY+'VI']
        key_sd=[KEY_prefix+KEY_MODULATORY+'iv',KEY_prefix+KEY_MODULATORY+'ii']
        key_tonic=[KEY_prefix+KEY_MODULATORY+'I',KEY_prefix+KEY_MODULATORY+'i']
        key_rel=[KEY_prefix+KEY_MODULATORY+'III',KEY_prefix+KEY_MODULATORY+'vi']

        total_key_mod=key_rel+key_tonic+key_sd+key_SD
        others_key_mod=[i for i in df.columns if KEY_prefix+KEY_MODULATORY in i and i not in total_key_mod]

        df[KEY_prefix+KEY_MODULATORY+'SD']=df[key_SD].sum(axis=1)
        df[KEY_prefix+KEY_MODULATORY+'sd']=df[key_sd].sum(axis=1)
        df[KEY_prefix+KEY_MODULATORY+'SubD']=df[KEY_prefix+KEY_MODULATORY+'sd'] + df[KEY_prefix+KEY_MODULATORY+'SD']
        df[KEY_prefix+KEY_MODULATORY+'T'] = df[key_tonic].sum(axis=1)
        df[KEY_prefix+KEY_MODULATORY+'rel'] = df[key_rel].sum(axis=1)
        df[KEY_prefix+KEY_MODULATORY+'Other'] = df[others_key_mod].sum(axis=1)
        # df.drop(total_key_mod+others_key_mod, axis = 1, inplace=True)

    def group_keys(self, df: DataFrame):
        df.update(df[[i for i in df.columns if KEY_prefix in i]].fillna(0))
        key_SD = [KEY_prefix+'IV'+KEY_PERCENTAGE, KEY_prefix+'II'+KEY_PERCENTAGE, KEY_prefix+'VI'+KEY_PERCENTAGE]
        key_sd = [KEY_prefix+'iv'+KEY_PERCENTAGE, KEY_prefix+'ii'+KEY_PERCENTAGE]
        key_tonic = [KEY_prefix+'I'+KEY_PERCENTAGE, KEY_prefix+'i'+KEY_PERCENTAGE]
        key_rel = [KEY_prefix+'III'+KEY_PERCENTAGE, KEY_prefix+'vi'+KEY_PERCENTAGE]

        total_key=key_rel+key_tonic+key_sd+key_SD
        others_key=[i for i in df.columns if KEY_prefix in i and i not in total_key and KEY_MODULATORY not in i]

        df[KEY_prefix+'SD'+KEY_PERCENTAGE]=df[key_SD].sum(axis=1)
        df[KEY_prefix+'sd'+KEY_PERCENTAGE]=df[key_sd].sum(axis=1)
        df[KEY_prefix+'SubD'+KEY_PERCENTAGE]=df[KEY_prefix+'sd'+KEY_PERCENTAGE] + df[KEY_prefix+'SD'+KEY_PERCENTAGE]
        df[KEY_prefix+'T'+KEY_PERCENTAGE] = df[key_tonic].sum(axis=1)
        df[KEY_prefix+'rel'+KEY_PERCENTAGE] = df[key_rel].sum(axis=1)
        df[KEY_prefix+'Other'+KEY_PERCENTAGE] = df[others_key].sum(axis=1)
        # df.drop(total_key+others_key, axis = 1, inplace=True)

    def join_degrees(self, df: DataFrame):
        total_degrees = [i for i in df.columns if '_Degree' in i]

        for part in self._post_config.instruments_to_keep:
            join_part_degrees(total_degrees, get_part_prefix(part), df)

        join_part_degrees(total_degrees, get_sound_prefix('voice'), df)
        # df.drop(total_degrees, axis = 1, inplace=True)

    def merge_voices(self, df):
        generic_sound_voice_prefix=get_sound_prefix('Voice')
        # voices_prefixes = [i + '_' for i in voices_list]
        # voice_prefix = voice+'_'
        for index, col in enumerate(df.columns.values):
                if any(voice in col for voice in voices_list_prefixes):
                    if ',' in df[VOICES][index]: #two or more voices
                        pass
                    else:
                        formatted_col=col
                        for voice_prefix in voices_list_prefixes:
                            formatted_col = formatted_col.replace(voice_prefix, generic_sound_voice_prefix)
                        if formatted_col in df:
                            df[formatted_col].fillna(df[col], inplace=True)
                        else:
                            df[formatted_col]=df[col]
                        df.drop(col, axis=1, inplace=True)
    
    def _final_data_processing(self, columns_order: List[str], composer_counter: list, novoices_counter: list, duetos_counter: list, df: DataFrame):
        df.sort_values(ARIA_ID, inplace=True)
        replace_nans(df)
        log_errors_and_shape(composer_counter, novoices_counter, duetos_counter, df)
        df = df.reindex(sorted(df.columns), axis=1)
        df = sort_columns(df, columns_order)
        dest_path=self.destination_route + "_processed" + ".csv"
        df.to_csv(dest_path, index=False)
        pinfo(f'\nData saved as {dest_path}')
   
    def preprocess_data(self, df: DataFrame):
        if 'Label_Passions' in df:
            del df['Label_Passions']

        if 'Label_Sentiment' in df:
            del df['Label_Sentiment']

        df = df[~df["Label_BasicPassion"].isnull()]
        df.replace(0.0, np.nan, inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        df.reset_index(inplace=True)

    def unbundle_instrumentation(self, df):
        for i, row in enumerate(df[INSTRUMENTATION]):
            for element in row.split(','):
                df.at[i, PRESENCE+'_'+element] = 1

    def _assign_labels(self, df: DataFrame):
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
        duetos_counter = []
        for i, comp in enumerate(df[COMPOSER].values):
            if pd.isnull(comp):
                composer_counter.append(df[FILE_NAME][i])
                df.drop(i, axis = 0, inplace=True)

        for i, voice in enumerate(df[VOICES].values):
            if pd.isnull(voice):
                novoices_counter.append(df[FILE_NAME][i])
                df.drop(i, axis = 0, inplace=True)

            # if ',' in voice:
            #     duetos_counter.append(df[FILE_NAME][i])
            #     df.drop(i, axis = 0, inplace=True)

        self.merge_voices(df)

        return composer_counter,novoices_counter,duetos_counter
    
    def delete_unwanted_columns(self, df):
        for inst in self._post_config.instruments_to_kill:
            df.drop([i for i in df.columns if 'Part'+inst in i], axis = 1, inplace=True)
        
        for inst in self._post_config.presence_to_kill:
            df.drop([i for i in df.columns if inst in i], axis = 1, inplace=True)

        df.drop([i for i in df.columns if get_part_prefix('Vn') in i], axis = 1, inplace=True)

        # Delete other unuseful columns
        df.drop([i for i in df.columns if i.startswith('HighestNote') or i.startswith('LowestNote')], axis = 1, inplace=True)
        df.drop([i for i in df.columns if '_Count' in i], axis = 1, inplace=True)
        df.drop([i for i in df.columns if i.startswith('SoundVoice_Dyn')], axis = 1, inplace=True)
        df.drop([i for i in df.columns if i.startswith(('FamilyWw', 'FamilyBr', 'EndOfThemeA', NUMBER_OF_BEATS))], axis = 1, inplace=True)
        df.drop([i for i in df.columns if i.endswith(('_Notes', '_SoundingMeasures', '_Syllables', '_NumberOfFilteredParts', NUMBER_OF_PARTS, '_NotesMean', 'Librettist', '_LargestIntervalAsc', '_LargestIntervalAll','_LargestIntervalDesc', '_NotesMean', 'Semitones_Sum', '_MeanInterval'))], axis = 1, inplace=True)
        df.drop([i for i in df.columns if i.endswith(('_HighestNote', '_LowestNote'))], axis = 1, inplace=True)
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


