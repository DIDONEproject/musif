########################################################################
# GENERATION MODULE
########################################################################
# This script is ment to read the intermediate DataFrame computed by the
# FeaturesExtractor and perform several computations while grouping the data
# based on several characteristics.
# Writes the final report files as well as generates the visualisations
########################################################################
import copy
import os
import sys
from itertools import permutations
from os import path
from typing import List, Optional

import numpy as np
import pandas as pd
from pandas import DataFrame
from tqdm import tqdm

from musif.common.constants import RESET_SEQ, VOICE_FAMILY, get_color
from musif.config import Configuration
from musif.extract.features import density, lyrics, scale, texture
from musif.extract.features.custom import harmony, scale_relative
from musif.extract.features.custom.__constants import *
from musif.extract.features.tempo import NUMBER_OF_BEATS
from musif.reports.calculations import make_intervals_absolute
from musif.reports.utils import remove_folder_contents
from .constants import *
from .tasks.common_tasks import Densities, Textures
from .tasks.harmony import Chords, Harmonic_data, Triple_harmonic_excel
from .tasks.intervals import Intervals, Intervals_types
from .tasks.melody_values import Melody_values
from .tasks.scale_degrees import Emphasised_scale_degrees


class FeaturesGenerator:
    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)
        self._logger = self._cfg.write_logger

    def generate_reports(self, data: DataFrame, num_factors: int = 0, main_results_path: str = '', parts_list: Optional[List[str]] = None) -> DataFrame:
        print(get_color('WARNING')+'\n---Starting reports generation ---\n'+ RESET_SEQ)
        self.parts_list = [] if parts_list is None else parts_list
        self.global_features = data
        self.num_factors_max = num_factors
        self.main_results_path = main_results_path
        self.sorting_lists = self._cfg.sorting_lists
        self._write()
            
    def _factor_execution(self, factor: int):
        global rows_groups
        global not_used_cols
        self.not_used_cols=not_used_cols
        self.rows_groups=rows_groups
        all_info=self.global_features
        main_results_path = os.path.join(self.main_results_path, 'reports')
        rg = copy.deepcopy(rows_groups)
        nuc = copy.deepcopy(not_used_cols)
        
        common_columns_df = all_info[metadata_columns]
        common_columns_df['Total analysed'] = 1.0

        tasks={}
        common_tasks={}
        harmony_tasks={}
        self.common = True #Flag to run common tasks only once
        self.voices=all_info.Voices

        print(get_color('INFO')+'\n' + str(factor) + " factor", end='\n'+RESET_SEQ)

        instruments = self.extract_instruments(all_info)

        self.prepare_common_dataframes(all_info, common_tasks, harmony_tasks, instruments)

        for instrument in tqdm(list(instruments), desc='Progress'):
            print(get_color('INFO')+'\nInstrument: ', instrument, end='\n\n'+RESET_SEQ)
            instrument_level = 'Part' + instrument + '_' if not self.IsVoice(instrument) else 'Family' + instrument + '_' 

            intervals_list, intervals_types_list, degrees_list, degrees_relative_list = self.find_columns(all_info, instrument_level)
            self.prepare_part_dataframes(all_info, common_columns_df, tasks, instrument_level, instrument, intervals_list, intervals_types_list, degrees_list, degrees_relative_list)
            
            additional_info, rg_groups = self.get_additional_info_and_groups(factor, rg) 

            results_path_factorx = path.join(main_results_path, 'Melody_' + instrument, str(
                factor) + " factor") if factor > 0 else path.join(main_results_path,'Melody_'+ instrument, "Data")
            if not os.path.exists(results_path_factorx):
                os.makedirs(results_path_factorx)
                
            if self.common:
                self.run_common_tasks(factor, main_results_path, rg, nuc, common_columns_df, common_tasks, harmony_tasks, tasks, additional_info, rg_groups, results_path_factorx)
            # # MULTIPROCESSING (one process per group (year, decade, city, country...))
            # if sequential: # 0 and 1 factors
            for groups in rg_groups:
                self._tasks_execution(rows_groups, not_used_cols, self._cfg, 
                    groups, results_path_factorx, additional_info, factor, common_columns_df, **tasks)
                rows_groups = rg
                not_used_cols = nuc

            # else: # from 2 factors
                # process_executor = concurrent.futures.ProcessPoolExecutor()
                # futures = [process_executor.submit(_group_execution, groups, results_path_factorx, additional_info, i, sorting_lists, Melody_values, intervals_info, absolute_intervals, Intervals_types, Emphasised_scale_degrees_info_A, Emphasised_scale_degrees_info_B, clefs_info, sequential) for groups in rg_groups]
                # kwargs = {'total': len(futures),'unit': 'it','unit_scale': True,'leave': True}
                # for f in tqdm(concurrent.futures.as_completed(futures), **kwargs):
                #     rows_groups = rg
                #     not_used_cols = nuc
                pass

    def find_notes_set(self, instruments):
        notes_set=set([])
        for instrument in instruments:
            if instrument.lower().startswith('vn'):
                notes_set.add(self.get_instrument_prefix(instrument) + '_Notes')
            else:
                notes_set.add(self.get_instrument_prefix(instrument) + '_NotesMean')
        return notes_set

    def prepare_part_dataframes(self, all_info, common_columns_df, tasks, Instrument_level, instrument, intervals_list, intervals_types_list, degrees_list, degrees_relative_list):
        if self._cfg.is_requested_module(interval):            
            intervals_info, intervals_types = self.extract_interval_columns(all_info, Instrument_level, intervals_list, intervals_types_list)
            intervals_info.dropna(how='all', axis=1, inplace=True)
            intervals_types.dropna(how='all', axis=1, inplace=True)
            tasks['intervals_info'] = intervals_info
            tasks['intervals_types'] = intervals_types

        if self._cfg.is_requested_module(ambitus):       
            try:     
                tasks['melody_values'] = self.extract_melody_colunms(all_info, Instrument_level).dropna(how='all', axis=1)
            except KeyError:
                self._cfg.write_logger.error(get_color('ERROR')+'Melody Values Dataframe could not be extracted.{}'.format(RESET_SEQ))                       
            

        if self.IsVoice(instrument):
            if self._cfg.is_requested_module(scale):            
                tasks['scale'] = self.Extract_scale_degrees_columns(all_info, Instrument_level, degrees_list).dropna(how='all', axis=1)
            if self._cfg.is_requested_module(scale_relative):            
                tasks['scale_relative'] = self.Extract_scale_degrees_columns(all_info, Instrument_level, degrees_relative_list).dropna(how='all', axis=1)
            tasks['clefs'] = self.get_clefs(all_info, common_columns_df)

    def prepare_common_dataframes(self, all_info, common_tasks, harmony_tasks, instruments):
        if self._cfg.is_requested_module(density) or self._cfg.is_requested_module(texture):
            notes_set = self.find_notes_set(instruments)    
            notes_df=all_info[list(notes_set)]
            common_tasks['notes']=notes_df
        
        if self._cfg.is_requested_module(density):
            density_df = self.capture_density_df(all_info, instruments)
            common_tasks['density']=density_df

        if self._cfg.is_requested_module(texture):
            textures_df = all_info[[i for i in all_info.columns if i.endswith('Texture')]].copy()
            common_tasks['textures'] = textures_df

        if self._cfg.is_requested_module(harmony):
            harmony_df, key_areas_df, chords_df, functions_dfs = self.capture_harmony_DFs(all_info)
            harmony_tasks['harmonic_data']=harmony_df
            harmony_tasks['key_areas']=key_areas_df
            harmony_tasks['chords']=chords_df
            harmony_tasks['functions']=functions_dfs
    def run_common_tasks(self, factor, main_results_path, rg, nuc, common_columns_df, common_tasks, harmony_tasks, tasks, additional_info, rg_groups, results_path_factorx):
        textures_densities_data_path = path.join(main_results_path, 'Texture&Density', str(
                factor) + " factor") if factor > 0 else path.join(main_results_path, 'Texture&Density', "Data")

        if not os.path.exists(textures_densities_data_path):
            os.makedirs(textures_densities_data_path)

        for groups in rg_groups:
            self._tasks_execution(self.rows_groups, self.not_used_cols, self._cfg,
                        groups, textures_densities_data_path, additional_info, factor, common_columns_df, **common_tasks)
                    
            if self._cfg.is_requested_module(harmony):
                harmony_data_path = path.join(main_results_path, 'Harmony', str(
                            factor) + " factor") if factor > 0 else path.join(main_results_path, 'Harmony', "Data")
                if not os.path.exists(harmony_data_path):
                     os.makedirs(harmony_data_path)
                        
                self._tasks_execution(self.rows_groups, self.not_used_cols, self._cfg,
                             groups, harmony_data_path, additional_info, factor, common_columns_df, **harmony_tasks)
                
        self.common = False #FLAG guarantees this is processed only once (all common files)
        
    def IsVoice(self, instrument):
        if instrument.lower()=='voice':
            return True
        return instrument.lower() in self.voices

    def get_clefs(self, all_info, common_columns_df):
        if ('Clef2' and 'Clef3') in common_columns_df.columns:
            common_columns_df.Clef2.replace('', np.nan, inplace=True)
            common_columns_df.Clef3.replace('', np.nan, inplace=True)
        clefs_info=copy.deepcopy(common_columns_df)
        clefs_set= {i for i in all_info.Clef1 + all_info.Clef2 + all_info.Clef3}
        for clef in clefs_set:
            clefs_info[clef] = 0
            for r, j in enumerate(clefs_info.iterrows()):
                clefs_info[clef].iloc[r] = float(len([i for i in clefs_info[['Clef1','Clef2','Clef3']].iloc[r] if i == clef]))
        clefs_info.replace('', np.nan, inplace=True)
        clefs_info.dropna(how='all', axis=1, inplace=True)
        return clefs_info

    def extract_instruments(self, all_info):
        instruments = set([])

        if self.parts_list:
            instruments = self.parts_list
        else:
            for aria in all_info['Scoring']:
                for a in aria.split(','):
                    instruments.add(a)

        instruments = self.capitalize_instruments(instruments)
        return instruments

    def capture_density_df(self, all_info, instruments):
        density_set = set([])
        for instrument in instruments:
            density_set.add(
                    self.get_instrument_prefix(instrument)  + '_SoundingDensity')
            density_set.add(
                    self.get_instrument_prefix(instrument)  + '_SoundingMeasures')
            if instrument.endswith('II'):
                continue
        density_set.add(NUMBER_OF_BEATS)
        density_df = all_info[list(density_set)]
        return density_df

    def capture_harmony_DFs(self, all_info):
        harmony_df=all_info[(
            [i for i in all_info.columns if HARMONIC_prefix in i] +
            [i for i in all_info.columns if CHORD_TYPES_prefix in i] +
            [i for i in all_info.columns if ADDITIONS_prefix in i]
            # + [i for i in all_info.columns if NUMERALS_prefix in i]
            )]
        key_areas_df=all_info[[i for i in all_info.columns if KEY_prefix in i or KEY_GROUPING in i ]]
        functions_dfs = all_info[[i for i in all_info.columns if NUMERALS_prefix in i] + [i for i in all_info.columns if CHORDS_GROUPING_prefix in i]]
        chords_df = all_info[[i for i in all_info.columns if CHORD_prefix in i and CHORD_TYPES_prefix not in i]]
        return harmony_df,key_areas_df,chords_df,functions_dfs

    def capitalize_instruments(self, instruments):
        return [instrument[0].upper()+instrument[1:]
                        for instrument in instruments]

    def get_additional_info_and_groups(self, factor, rg):
        additional_info = {ARIA_LABEL: [TITLE],
                                TITLE: [ARIA_LABEL]}

        if factor == 0:
            rows_groups = {ARIA_ID: ([], "Alphabetic")}
            rg_keys = [rg[r][0] if rg[r][0] != [] else r for r in rg]
            for r in rg_keys:
                if type(r) == list:
                    self.not_used_cols += r
                else:
                   self.not_used_cols.append(r)
            additional_info = [ARIA_LABEL, TITLE, COMPOSER, YEAR]

        rg_groups = [[]]
        if factor >= 2:  # 2 factors or more
            rg_groups = list(permutations(
                    list(forbiden_groups.keys()), factor - 1))[4:]

            if factor > 2:
                prohibited = [COMPOSER, OPERA]
                for g in rg_groups:
                    if ARIA_ID in g:
                        g_rest = g[g.index(ARIA_ID):]
                        if any(p in g_rest for p in prohibited):
                            rg_groups.remove(g)
                    elif ARIA_LABEL in g:
                        g_rest = g[g.index(ARIA_LABEL):]
                        if any(p in g_rest for p in prohibited):
                            rg_groups.remove(g)
            rg_groups = [r for r in rg_groups if r[0]
                                in list(metadata_columns)]
                            
        return additional_info,rg_groups

    def Extract_scale_degrees_columns(self, all_info, catch, degrees_list):
        scale_degrees_info=all_info[[c for c in degrees_list if catch in c]]
        scale_degrees_info.columns = [c.replace(catch, '').replace('Degree', '').replace('_Count', '') for c in scale_degrees_info.columns]
        return scale_degrees_info

    def find_columns(self, all_info, Instr_level):
        intervals_list = []
        intervals_types_list = []
        degrees_list = []
        degrees_relative_list = []

        for col in all_info.columns:
            if col.startswith(Instr_level+'Interval_'):
                intervals_list.append(col)
            elif 'Degree' in col and col.endswith('_Count'):
                degrees_list.append(col)
            elif 'Degree' in col and 'relative' in col and not 'Per' in col:
                degrees_relative_list.append(col)
            elif (col.startswith(Instr_level+'Intervals') or col.startswith(Instr_level+'Leaps') or col.startswith(Instr_level+'Stepwise')) and col.endswith('_Count'):
                intervals_types_list.append(col)

            intervals_types_list.append(Instr_level + interval.REPEATED_NOTES_COUNT)

        return intervals_list, intervals_types_list, degrees_list, degrees_relative_list

    def extract_melody_colunms(self, all_info, catch):
        melody_values_list = get_melody_list(catch)
        if catch + lyrics.SYLLABIC_RATIO in all_info.columns:
            melody_values_list.append(catch + lyrics.SYLLABIC_RATIO)
            
        melody_values=all_info[melody_values_list]  
        melody_values.columns = [c.replace(catch, '').replace('_Count', '')
                                for c in melody_values.columns]
        return melody_values

    def extract_interval_columns(self, all_info, catch, intervals_list, intervals_types_list):
        intervals_info=all_info[intervals_list]
        intervals_info.columns = [c.replace(catch+'Interval_', '').replace('_Count', '')
                                    for c in intervals_info.columns]
        intervals_types=all_info[intervals_types_list]
        intervals_types.columns = [c.replace(catch, '').replace('Intervals', '').replace('_Count', '')
                                    for c in intervals_types.columns]
                            
        return intervals_info,intervals_types

    def get_instrument_prefix(self, instrument: list):
        if instrument.lower().startswith('vn'):  # Violins are the exception in which we don't take Sound level data
            prefix = 'Part'
        elif self.IsVoice(instrument):
            prefix = 'Family'
            instrument=VOICE_FAMILY.capitalize()
        else:
            prefix = 'Sound'
            instrument=instrument.replace('I','')
        
        inst=prefix+instrument
        return inst

#####################################################################

    def _tasks_execution(self, rg: dict, nuc:list, _cfg: Configuration, groups: list, results_path_factorx: str, additional_info, factor: int, common_columns_df: DataFrame, **kwargs): 
    
        global rows_groups
        global not_used_cols
        rows_groups=rg
        not_used_cols=nuc

        visualiser_lock = True #remve with threads

        if groups:
            # if sequential:
            results_path = path.join(results_path_factorx, '_'.join(groups))
            if not os.path.exists(results_path):
                os.mkdir(results_path)
        else:
            results_path = results_path_factorx

        if os.path.exists(path.join(results_path, 'visualisations')):
            remove_folder_contents(
                path.join(results_path, 'visualisations'))
        else:
            os.makedirs(path.join(results_path, 'visualisations'))

        # MUTITHREADING
        try:
            # executor = concurrent.futures.ThreadPoolExecutor()
            # visualiser_lock = threading.Lock()
            # futures = []

            pre_string='-'.join(groups) + str(factor) + '_factor_'
            if 'melody_values' in kwargs:
                melody_values = pd.concat([common_columns_df,  kwargs["melody_values"]], axis=1)
                Melody_values(rows_groups, not_used_cols, factor, _cfg, melody_values, results_path, pre_string , "Melody_Values.xlsx",
                        visualiser_lock, additional_info, True if factor == 0 else False, groups if groups != [] else None)
            if 'density' in kwargs:
                density_df = pd.concat(
                    [common_columns_df, kwargs["density"], kwargs["notes"]], axis=1)
                Densities(rows_groups, not_used_cols, factor, _cfg, density_df, results_path, pre_string, "Densities", visualiser_lock, groups if groups != [] else None, additional_info)
            
            if 'textures' in kwargs:
                textures_df = pd.concat(
                [common_columns_df, kwargs["textures"], kwargs["notes"]], axis=1)
                Textures(rows_groups, not_used_cols, factor, _cfg, textures_df, results_path, pre_string, "Textures", visualiser_lock, groups if groups != [] else None, additional_info)
            
            if 'intervals_info' in kwargs:
                intervals_info=pd.concat([common_columns_df, kwargs["intervals_info"]], axis=1)
                Intervals(rows_groups, not_used_cols, factor, _cfg, intervals_info, pre_string, "Intervals",
                                    _cfg.sorting_lists["Intervals"], results_path, visualiser_lock, additional_info, groups if groups != [] else None)
                absolute_intervals=make_intervals_absolute(intervals_info)
                Intervals(rows_groups, not_used_cols, factor, _cfg, absolute_intervals, pre_string , "Intervals_absolute",
                                _cfg.sorting_lists["Intervals_absolute"], results_path, visualiser_lock, additional_info, groups if groups != [] else None)
            
            if 'intervals_types' in kwargs:
                intervals_types = pd.concat([common_columns_df, kwargs["intervals_types"]], axis=1)
                Intervals_types(rows_groups, not_used_cols, factor, _cfg, intervals_types, results_path, pre_string, "Interval_types", visualiser_lock, groups if groups != [] else None, additional_info)
            
            if 'scale' in kwargs and not kwargs['scale'].empty:
                emphasised_scale_degrees_info_A = pd.concat([common_columns_df,kwargs['scale']], axis=1)
                Emphasised_scale_degrees(rows_groups, not_used_cols, factor, _cfg, emphasised_scale_degrees_info_A, pre_string,  "Scale_degrees", results_path, visualiser_lock, groups if groups != [] else None, additional_info)
            
            if 'scale_relative' in kwargs:
                emphasised_scale_degrees_info_B = pd.concat([common_columns_df,kwargs['scale_relative']], axis=1)
                Emphasised_scale_degrees(rows_groups, not_used_cols, factor, _cfg, emphasised_scale_degrees_info_B, pre_string, "Scale_degrees_relative", results_path, visualiser_lock, groups if groups != [] else None, additional_info)
           
            if 'clefs' in kwargs:
                clefs_info= pd.concat([common_columns_df,kwargs['clefs']], axis=1)
                Intervals(rows_groups, not_used_cols, factor, _cfg, clefs_info, pre_string, "Clefs_in_voice",
                                _cfg.sorting_lists["Clefs"], results_path, visualiser_lock, additional_info, groups if groups != [] else None)
            if 'harmonic_data' in kwargs:
                harmony_df= pd.concat([common_columns_df , kwargs['harmonic_data']], axis=1)
                Harmonic_data(rows_groups, not_used_cols, factor, _cfg, harmony_df, pre_string, "Harmonic_data", results_path, visualiser_lock, additional_info, groups if groups != [] else None)
            
            if 'chords' in kwargs:
                chords = pd.concat([common_columns_df, kwargs['chords']], axis=1)
                Chords(rows_groups, not_used_cols, factor, _cfg, chords, results_path, pre_string,  "Chords", visualiser_lock, groups if groups != [] else None, additional_info)
            
            if 'functions' in kwargs:
                functions = pd.concat([common_columns_df, kwargs['functions']], axis=1)
                Triple_harmonic_excel(rows_groups, not_used_cols, factor, _cfg, functions, results_path, pre_string, 'Harmonic_functions', visualiser_lock, groups if groups != [] else None, additional_info)
            
            if 'key_areas' in kwargs:
                key_areas= pd.concat([common_columns_df,kwargs['key_areas']], axis=1)
                # Triple_harmonic_excel(rows_groups, not_used_cols, factor, _cfg, key_areas, results_path, pre_string, "Key_Areas", visualiser_lock, groups if groups != [] else None, additional_info)
                
                # wait for all
                # if sequential:
                # kwargs = {'total': len(futures), 'unit': 'it',
                #             'unit_scale': True, 'leave': True}
                # for f in tqdm(concurrent.futures.as_completed(futures), **kwargs):
                #     pass
                # else:
                #     for f in concurrent.futures.as_completed(futures):
                #         pass

        except KeyboardInterrupt:
            self._logger.error('\033[93mAn error ocurred during the report generation process. \033[37m')
            sys.exit(2)


    def _write(self):

        # Start factor generation
        for factor in range(1, self.num_factors_max + 1):
            self._factor_execution(factor)
