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
from itertools import permutations
from os import path
from typing import List, Optional, Tuple

from musif.extract.features import ambitus, density, interval, key, scale, lyrics, metadata, texture
from musif.extract.features.custom import harmony

import numpy as np
import pandas as pd
from musif.common.constants import VOICE_FAMILY
from config import Configuration
from pandas import DataFrame
from tqdm import tqdm

from .constants import *
from .tasks import _tasks_execution


class FeaturesGenerator:

    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)
        self._logger = self._cfg.write_logger
        

    def generate_reports(self, df: DataFrame, num_factors: int = 0, main_results_path: str = '', parts_list: Optional[List[str]] = None) -> DataFrame:
        print('\n---Starting reports generation ---\n')
        self.parts_list = [] if parts_list is None else parts_list
        self.global_features = df
        self.num_factors_max = num_factors
        self.main_results_path = main_results_path
        self.sorting_lists = self._cfg.sorting_lists
        self._write(self.global_features)
            
    def _factor_execution(self, all_info: DataFrame, factor: int, parts_list: list, main_results_path: str, sorting_lists: dict, _cfg: Configuration):
        global rows_groups
        global not_used_cols
        # global cfg
        # cfg = _cfg
        main_results_path = os.path.join(main_results_path, 'results')
        rg = copy.deepcopy(rows_groups)
        nuc = copy.deepcopy(not_used_cols)

        # 1. Split all the dataframes to work individually
        common_columns_df = all_info[metadata_columns]

        common_columns_df['Total analysed'] = 1.0

        textures_df = []
        density_set = set([])
        notes_set=set([])
        instruments = set([])
        clefs_info=pd.DataFrame()
        textures_df=pd.DataFrame()
        melody_values=pd.DataFrame()
        if parts_list:
            instruments = parts_list
        else:
            for aria in all_info['Scoring']:
                for a in aria.split(','):
                    instruments.add(a)

        instruments = [instrument[0].upper()+instrument[1:]
                        for instrument in instruments]

        # Inizalizing new dataframes and defining those that don't depends on each part
        if ('Clef2' and 'Clef3') in common_columns_df.columns:
            common_columns_df.Clef2.replace('', np.nan, inplace=True)
            common_columns_df.Clef3.replace('', np.nan, inplace=True)
        clefs = None
        # Getting general data that requires all info but is ran only once

        for instrument in instruments:
            if instrument.lower().startswith('vn'):  # Violins are the exception in which we don't take Sound level data
                catch = 'Part'
                notes_set.add(catch + instrument + '_Notes')

            elif instrument.lower() in all_info.Voices[0]:
                catch='Family'
                instrument=VOICE_FAMILY.capitalize()
                clefs=True # We want clefs only when voice is required
                notes_set.add(catch + instrument + '_NotesMean')

            else:
                catch = 'Sound'
                if instrument.endswith('II'):
                    continue
                instrument = instrument.replace('I', '')
                notes_set.add(catch + instrument.replace('I', '') + '_NotesMean')

        if self._cfg.is_required_module(density) or self._cfg.is_required_module(texture):
            notes_df=all_info[list(notes_set)]
        
        # Getting different features
        if self._cfg.is_required_module(density):
            density_set.add(
                catch + instrument + '_SoundingDensity')
            density_set.add(
                catch + instrument + '_SoundingMeasures')
            density_set.add('NumberOfBeats')
            density_df = all_info[list(density_set)]

        if self._cfg.is_required_module(texture):
            textures_df = all_info[[i for i in all_info.columns if i.endswith('Texture')]]
        

        # Getting harmonic features
        if self._cfg.is_required_module(harmony):
            harmony_df=all_info[[i for i in all_info.columns if 'harmonic' in i.lower()]]
            key_areas=all_info[[i for i in all_info.columns if 'Key' in i]]

            #esto son las funciones armonmicas (agrupaciones del resto de cosas) -> Segunda mita (parte B y C) del excel de numerals
            functions_dfs = all_info[[i for i in all_info.columns if 'Numerals' in i] + [i for i in all_info.columns if 'Chords_Grouping' in i]]
            
            chords_df = all_info[[i for i in all_info.columns if 'chords' in i.lower() and not 'grouping' in i.lower()]]
            
            #Not used by now:
            chords_types = all_info[[i for i in all_info.columns if 'Chord_types' in i]]

        
        # Getting Voice Clefs info in case Voices are required
        if clefs:
            clefs_info=copy.deepcopy(common_columns_df)
            clefs_set= {i for i in all_info.Clef1 + all_info.Clef2 + all_info.Clef3}
            for clef in clefs_set:
                clefs_info[clef] = 0
                for r, j in enumerate(clefs_info.iterrows()):
                    clefs_info[clef].iloc[r] = float(len([i for i in clefs_info[['Clef1','Clef2','Clef3']].iloc[r] if i == clef]))
            clefs_info.replace('', np.nan, inplace=True)
            clefs_info.dropna(how='all', axis=1, inplace=True)

        FLAG=True #Flag to run common tasks only once
        
        print('\n' + str(factor) + " factor")

        # CAPTURING FEATURES that depend total or partially on each part
        for instrument in tqdm(list(instruments), desc='Progress'):
            print('\nInstrument: ', instrument, end='\n\n')
            intervals_list = []
            intervals_types_list = []
            emphasised_A_list = []
                    

            catch = 'Part' + instrument + '_'
            # List of columns for melody parameters

            melody_values_list = [catch+interval.INTERVALLIC_MEAN, catch+interval.INTERVALLIC_STD, catch+interval.ABSOLUTE_INTERVALLIC_MEAN, catch+interval.ABSOLUTE_INTERVALLIC_STD, catch+interval.TRIMMED_ABSOLUTE_INTERVALLIC_MEAN,catch+interval.TRIMMED_ABSOLUTE_INTERVALLIC_STD,
                            catch+interval.TRIMMED_INTERVALLIC_STD,catch+interval.TRIMMED_INTERVALLIC_MEAN, catch+interval.ABSOLUTE_INTERVALLIC_TRIM_DIFF, catch+interval.ABSOLUTE_INTERVALLIC_TRIM_RATIO, catch+ interval.LARGEST_ASC_INTERVAL_SEMITONES, catch+ interval.LARGEST_ASC_INTERVAL,
                            catch+interval.LARGEST_DESC_INTERVAL_SEMITONES, catch+ interval.LARGEST_DESC_INTERVAL, catch + ambitus.HIGHEST_INDEX, catch + ambitus.LOWEST_NOTE, catch + ambitus.LOWEST_MEAN_NOTE, 
                            catch + ambitus.LOWEST_MEAN_INDEX, catch + ambitus.HIGHEST_MEAN_NOTE, catch + ambitus.HIGHEST_NOTE, catch + ambitus.LOWEST_INDEX, catch + ambitus.HIGHEST_MEAN_INDEX, catch + ambitus.LARGEST_INTERVAL, catch + ambitus.LARGEST_SEMITONES,
                            catch + ambitus.SMALLEST_INTERVAL, catch + ambitus.SMALLEST_SEMITONES, catch + ambitus.MEAN_INTERVAL, catch + ambitus.MEAN_SEMITONES]

            if catch + lyrics.SYLLABIC_RATIO in all_info.columns:
                melody_values_list.append(catch + lyrics.SYLLABIC_RATIO)

            #Getting list of columns for intervals and scale degrees
            for col in all_info.columns:
                if col.startswith(catch+'Interval_'):
                    intervals_list.append(col)
                elif col.startswith(catch+'Degree') and col.endswith('_Count'):
                    emphasised_A_list.append(col)
                elif (col.startswith(catch+'Intervals') or col.startswith(catch+'Leaps') or col.startswith(catch+'Stepwise')) and col.endswith('_Count'):
                    intervals_types_list.append(col)
            
            # Joining common info and part info, renaming columns for excel writing
            
            # INTERVALS
            if self._cfg.is_required_module(interval):            
                intervals_types_list.append(catch + interval.REPEATED_NOTES_COUNT)
                intervals_info=all_info[intervals_list]
                intervals_info.columns = [c.replace(catch+'Interval_', '').replace('_Count', '')
                                    for c in intervals_info.columns]
                intervals_types=all_info[intervals_types_list]
                intervals_types.columns = [c.replace(catch, '').replace('Intervals', '').replace('_Count', '')
                                    for c in intervals_types.columns]
            # MELODY
            if self._cfg.is_required_module(ambitus):            
                melody_values=all_info[melody_values_list]  
                melody_values.columns = [c.replace(catch, '').replace('_Count', '')
                                for c in melody_values.columns]
            # KEYS
            if self._cfg.is_required_module(scale):            
                emphasised_scale_degrees_info_A=all_info[emphasised_A_list]
                emphasised_scale_degrees_info_A.columns = [c.replace(catch, '').replace('Degree', '').replace('_Count', '')
                    for c in emphasised_scale_degrees_info_A.columns]
                emphasised_scale_degrees_info_B = copy.deepcopy(common_columns_df)

            # Dropping nans
            melody_values = melody_values.dropna(how='all', axis=1)
            intervals_info.dropna(how='all', axis=1,inplace=True)
            intervals_types.dropna(
                how='all', axis=1,inplace=True)
            emphasised_scale_degrees_info_A.dropna(
                how='all', axis=1,inplace=True)
            emphasised_scale_degrees_info_B.dropna(
                how='all', axis=1,inplace=True)

            # Get the additional_info dictionary (special case if there're no factors)
            additional_info = {ARIA_LABEL: [TITLE],
                                TITLE: [ARIA_LABEL]}  # ONLY GROUP BY ARIA

            if factor == 0:
                rows_groups = {ARIA_ID: ([], "Alphabetic")}
                rg_keys = [rg[r][0] if rg[r][0] != [] else r for r in rg]
                for r in rg_keys:
                    if type(r) == list:
                        not_used_cols += r
                    else:
                        not_used_cols.append(r)
                # It a list, so it is applicable to all grouppings
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
                                in list(metadata_columns)]  # ???

            results_path_factorx = path.join(main_results_path, 'Melody_' + instrument, str(
                factor) + " factor") if factor > 0 else path.join(main_results_path,'Melody_'+ instrument, "Data")
            if not os.path.exists(results_path_factorx):
                os.makedirs(results_path_factorx)
                
            # FLAG ensures this part is only run once, not for every instrument. This executes common tasks for any instrument
            if FLAG:
                textures_densities_data_path = path.join(main_results_path, 'Texture&Density', str(
                factor) + " factor") if factor > 0 else path.join(main_results_path, 'Texture&Density', "Data")

                if not os.path.exists(textures_densities_data_path):
                    os.makedirs(textures_densities_data_path)

                for groups in rg_groups:
                    _tasks_execution(rows_groups, not_used_cols, cfg,
                        groups, textures_densities_data_path, additional_info, factor, common_columns_df, notes_df=notes_df, density_df=density_df, textures_df=textures_df, harmony_df=harmony_df, key_areas=key_areas, chords=chords_df)
                    
                    if self._cfg.is_required_module(harmony):
                        harmony_data_path = path.join(main_results_path, 'Harmony', str(
                            factor) + " factor") if factor > 0 else path.join(main_results_path, 'Harmony', "Data")
                        if not os.path.exists(harmony_data_path):
                             os.makedirs(harmony_data_path)
                        
                        _tasks_execution(rows_groups, not_used_cols, self._cfg,
                            groups, harmony_data_path, additional_info, factor, common_columns_df, harmony_df=harmony_df, key_areas=key_areas, chords=chords_df, functions=functions_dfs)
                FLAG=False #FLAG guarantees this is processed only once (all common files)

            # # MULTIPROCESSING (one process per group (year, decade, city, country...))
            # if sequential: # 0 and 1 factors
            for groups in rg_groups:
                _tasks_execution(rows_groups, not_used_cols, self._cfg, 
                    groups, results_path_factorx, additional_info, factor, common_columns_df, melody_values=melody_values, intervals_info=intervals_info, intervals_types=intervals_types, clefs_info=clefs_info,emphasised_scale_degrees_info_A = emphasised_scale_degrees_info_A, key_areas=key_areas)
                rows_groups = rg
                not_used_cols = nuc
            # else: # from 2 factors
                # process_executor = concurrent.futures.ProcessPoolExecutor()
                # futures = [process_executor.submit(_group_execution, groups, results_path_factorx, additional_info, i, sorting_lists, Melody_values, intervals_info, absolute_intervals, Intervals_types, Emphasised_scale_degrees_info_A, Emphasised_scale_degrees_info_B, clefs_info, sequential) for groups in rg_groups]
                # kwargs = {'total': len(futures),'unit': 'it','unit_scale': True,'leave': True}
                # for f in tqdm(concurrent.futures.as_completed(futures), **kwargs):
                #     rows_groups = rg
                #     not_used_cols = nuc

    def _write(self, all_info: DataFrame):
        # Start factor generation
        for factor in range(1, self.num_factors_max + 1):
            self._factor_execution(
                all_info, factor, self.parts_list, self.main_results_path, self.sorting_lists, self._cfg)
