########################################################################
# GENERATION MODULE
########################################################################

# This script is meant to read the intermediate DataFrame computed by the
# FeaturesExtractor and perform several computations while grouping the data
# based on some characteristics.
# Writes the final report files as well as generates visualisations forthe data
########################################################################

import copy
import os
import sys
from itertools import permutations
from os import path

import numpy as np
import pandas as pd
from musif.common.constants import VOICE_FAMILY
from musif.config import Configuration
from musif.extract.features import (density, harmony, lyrics, scale,
                                    scale_relative, texture)
from musif.extract.features.tempo.constants import NUMBER_OF_BEATS
from musif.logs import lerr, perr
from musif.reports.calculations import make_intervals_absolute
from musif.reports.utils import (capitalize_instruments,
                                 remove_folder_contents)
from pandas import DataFrame
from tqdm import tqdm

from ..logs import pinfo
from .constants import *
from .tasks.common_tasks import Densities, Textures
from .tasks.harmony import Harmonic_analysis
from .tasks.intervals import Intervals, Intervals_types
from .tasks.melody_values import Melody_values
from .tasks.scale_degrees import Emphasised_scale_degrees

COMMON_DF = 'common_df'

class FeaturesGenerator:
    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)

    def generate_reports(self, data: DataFrame, main_results_path: str, num_factors: int = 0, visualizations=False) -> DataFrame:
        pinfo('\n'+'--- Starting reports generation ---\n'.center(120, ' '))
        self.parts_list = [] if self._cfg.parts_filter is None else self._cfg.parts_filter
        self.visualizations=visualizations
        pinfo('Visualizations are enabled' if self.visualizations else 'Visualizations are disabled'+'.\n')
        
        self.global_features = data
        self.num_factors_max = num_factors
        self.main_results_path = main_results_path
        self.sorting_lists = self._cfg.sorting_lists
        self._write()

    def _write(self):
        for factor in range(1, self.num_factors_max + 1):
            self._Factor_Execution(factor)
           
    def _Factor_Execution(self, num_factors: int = 0):
        global rows_groups
        global not_used_cols
        self.not_used_cols=not_used_cols
        self.rows_groups=rows_groups
        self.main_results_path = os.path.join(self.main_results_path, 'reports')
        self.metadata_columns=metadata_columns
        all_info = self.global_features
        self.voices=all_info.Voices
        
        tasks={}
        common_columns_df = self._find_common_columns(all_info)
        pinfo('\n' + str(num_factors) + " factor" + "\n")
        instruments = self._extract_instruments(all_info)
        self._rename_singers(all_info)

        common_tasks, harmony_tasks=self._prepare_common_dataframes(all_info, instruments)

        additional_info, rg_groups = self._get_additional_info_and_groups(num_factors, self.rows_groups) 

        self._run_common_tasks(num_factors, common_columns_df, common_tasks, harmony_tasks, additional_info, rg_groups)

        for instrument in tqdm(list(instruments), desc='Instruments'):
            if instrument.lower() in singers_list:
                instrument = 'Voice'
            pinfo(f'\nInstrument:\t{instrument}' + '\n')

            instrument_level = 'Part' + instrument + '_'
            intervals_list, intervals_types_list, degrees_list, degrees_relative_list = self._find_interval_degree_columns(all_info, instrument_level)
            self._prepare_part_dataframes(all_info, common_columns_df, tasks, instrument_level, instrument, intervals_list, intervals_types_list, degrees_list, degrees_relative_list)
            
            self.results_path_factorx = path.join(self.main_results_path, 'Melody_' + instrument, str(
                num_factors) + " factor") if num_factors > 0 else path.join(self.main_results_path,'Melody_'+ instrument, "Data")
            if not os.path.exists(self.results_path_factorx):
                os.makedirs(self.results_path_factorx)

            # if sequential: # 0 and 1 factors
            for groups in rg_groups:
                try:
                    self._tasks_execution(self.rows_groups, self.not_used_cols, self._cfg, 
                        groups, additional_info, num_factors, common_columns_df, **tasks)
                    pass
                    # rows_groups = rg
                    # not_used_cols = nuc
                except KeyError as e:
                    perr('One or more of the features could not be found in the input dataframe: '.format(e))
            # else: # from 2 factors
                # process_executor = concurrent.futures.ProcessPoolExecutor()
                # futures = [process_executor.submit(_group_execution, groups, results_path_factorx, additional_info, i, sorting_lists, Melody_values, intervals_info, absolute_intervals, Intervals_types, Emphasised_scale_degrees_info_A, Emphasised_scale_degrees_info_B, clefs_info, sequential) for groups in rg_groups]
                # kwargs = {'total': len(futures),'unit': 'it','unit_scale': True,'leave': True}
                # for f in tqdm(concurrent.futures.as_completed(futures), **kwargs):
                #     rows_groups = rg
                #     not_used_cols = nuc

    def _find_common_columns(self, all_info):
        common_columns_df= pd.DataFrame()
        columns_to_remove=[]
        for column in self.metadata_columns:
            info=all_info.get(column)
            if info is not None:
                common_columns_df=pd.concat((common_columns_df, info), axis=1)
            else:
                if column in self.not_used_cols:
                    del self.not_used_cols[column]
                if column in self.rows_groups:
                    del self.rows_groups[column]
                columns_to_remove.append(column)
                perr(f'No column was found for {column} in the df!')
        self.metadata_columns=list(set(self.metadata_columns)-set(columns_to_remove))
        common_columns_df['Total analysed'] = 1.0
        return common_columns_df

    def _find_notes_set(self, instruments):
        notes_set=set([])
        for instrument in instruments:
            if instrument.lower().startswith('vn'):
                notes_set.add(self._get_instrument_prefix(instrument) + '_Notes')
            else:
                notes_set.add(self._get_instrument_prefix(instrument) + '_NotesMean')
        return notes_set

    def _prepare_part_dataframes(self, all_info, common_columns_df, tasks, Instrument_level, instrument, intervals_list, intervals_types_list, degrees_list, degrees_relative_list):
        if self._cfg.is_requested_module(interval):            
            intervals_info, intervals_types = self._find_interval_columns(all_info, Instrument_level, intervals_list, intervals_types_list)
            intervals_info.dropna(how='all', axis=1, inplace=True)
            intervals_types.dropna(how='all', axis=1, inplace=True)
            if not intervals_info.empty:
                tasks['intervals_info'] = intervals_info
            if not intervals_types.empty:
                tasks['intervals_types'] = intervals_types

        if self._cfg.is_requested_module(ambitus):       
            try:     
                tasks['melody_values'] = self._find_melody_columns(all_info, Instrument_level).dropna(how='all', axis=1)
            except KeyError as e:                 
                perr('Melody Values information could not be extracted'.format(e))

        if self._IsVoice(instrument):
            if self._cfg.is_requested_module(scale):            
                tasks['scale'] = self._find_scale_degrees_columns(all_info, Instrument_level, degrees_list).dropna(how='all', axis=1)
            if self._cfg.is_requested_module(scale_relative):            
                tasks['scale_relative'] = self._find_scale_degrees_columns(all_info, Instrument_level, degrees_relative_list).dropna(how='all', axis=1)
            tasks['clefs'] = self._get_clefs(all_info, common_columns_df)

    def _prepare_common_dataframes(self, all_info, instruments):
        common_tasks={}
        harmony_tasks={}
        if self._cfg.is_requested_module(density) or self._cfg.is_requested_module(texture):
            notes_set = self._find_notes_set(instruments)    
            notes_df=all_info[list(notes_set)]
            common_tasks['notes']=notes_df
        
        if self._cfg.is_requested_module(density):
            density_df = self._find_density_columns(all_info, instruments)
            common_tasks['density']=density_df

        if self._cfg.is_requested_module(texture):
            textures_df = all_info[[i for i in all_info.columns if i.endswith('Texture')]].copy()
            common_tasks['textures'] = textures_df

        if self._cfg.is_requested_module(harmony):
            harmony_df, key_areas_df, chords_df, functions_dfs = self._find_harmony_columns(all_info)
            harmony_tasks['harmonic_data']=harmony_df
            harmony_tasks['key_areas']=key_areas_df
            harmony_tasks['chords']=chords_df
            harmony_tasks['functions']=functions_dfs
        
        return common_tasks, harmony_tasks

    def _run_common_tasks(self, factor, common_columns_df, common_tasks, harmony_tasks, additional_info, rg_groups):
        pinfo('\n'+'--- Generating common reports: Density, Texture and Harmony ---'.center(120))

        for groups in rg_groups:
            
            if self._cfg.is_requested_module(texture) or self._cfg.is_requested_module(density):
                textures_densities_data_path = path.join(self.main_results_path, 'Texture&Density', str(
                        factor) + " factor") if factor > 0 else path.join(self.main_results_path, 'Texture&Density', "Data")
                if not os.path.exists(textures_densities_data_path):
                    os.makedirs(textures_densities_data_path)

                self._tasks_execution(self.rows_groups, self.not_used_cols, self._cfg,
                            groups, additional_info, factor, common_columns_df,results_path= textures_densities_data_path, **common_tasks)
            
            if self._cfg.is_requested_module(harmony):
                harmony_data_path = path.join(self.main_results_path, 'Harmony', str(
                            factor) + " factor") if factor > 0 else path.join(self.main_results_path, 'Harmony', "Data")
                if not os.path.exists(harmony_data_path):
                     os.makedirs(harmony_data_path)

                self._tasks_execution(self.rows_groups, self.not_used_cols, self._cfg,
                             groups, additional_info, factor, common_columns_df,results_path=harmony_data_path, **harmony_tasks)
    
    def _rename_singers(self, all_info):
        for c in all_info.columns:
            if any(i.capitalize() in c for i in singers_list):
                for s in singers_list:
                    all_info.rename(columns={c:c.replace(s.capitalize(),'Voice')}, inplace=True)
            
    def _IsVoice(self, instrument):
        if instrument.lower()=='voice':
            return True
        return instrument.lower() in self.voices

    def _get_clefs(self, all_info, common_columns_df):
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

    def _extract_instruments(self, all_info):
        instruments = set([])

        if self.parts_list:
            instruments = self.parts_list
        else:
            for aria in all_info['Scoring']:
                for a in aria.split(','):
                    instruments.add(a)

        instruments = capitalize_instruments(instruments)
        
        return instruments

    def _find_density_columns(self, all_info, instruments):
        density_set = set([])
        for instrument in instruments:
            density_set.add(
                    self._get_instrument_prefix(instrument)  + '_SoundingDensity')
            density_set.add(
                    self._get_instrument_prefix(instrument)  + '_SoundingMeasures')
            if instrument.endswith('II'):
                continue
        density_set.add(NUMBER_OF_BEATS)
        density_df = all_info[list(density_set)]
        return density_df

    def _find_harmony_columns(self, all_info):
        harmony_df=all_info[(
            [i for i in all_info.columns if harmony.constants.HARMONIC_prefix in i] +
            [i for i in all_info.columns if harmony.constants.CHORD_TYPES_prefix in i] +
            [i for i in all_info.columns if harmony.constants.ADDITIONS_prefix in i]
            )]
        key_areas_df=all_info[[i for i in all_info.columns if harmony.constants.KEY_prefix in i or harmony.constants.KEY_GROUPING in i ]]
        functions_dfs = all_info[[i for i in all_info.columns if harmony.constants.NUMERALS_prefix in i and i.endswith('_Count')] + [i for i in all_info.columns if harmony.constants.CHORDS_GROUPING_prefix in i and i.endswith('_Count')]]
        chords_df = all_info[[i for i in all_info.columns if harmony.constants.CHORD_prefix in i and harmony.constants.CHORD_TYPES_prefix not in i and i.endswith('_Count')]]
        return harmony_df,key_areas_df,chords_df,functions_dfs

    def _find_scale_degrees_columns(self, all_info, catch, degrees_list):
        scale_degrees_info=all_info[[c for c in degrees_list if catch in c]]
        scale_degrees_info.columns = [c.replace(catch, '').replace('Degree', '').replace('_Count', '') for c in scale_degrees_info.columns]
        return scale_degrees_info

    def _find_interval_degree_columns(self, all_info, Instr_level):
        intervals_list = []
        intervals_types_list = []
        degrees_list = []
        degrees_relative_list = []

        for col in all_info.columns:
            if (col.startswith(Instr_level+'Intervals') or col.startswith(Instr_level+'Leaps') or col.startswith(Instr_level+'Stepwise')) and col.endswith('_Count'):
                intervals_types_list.append(col)
            elif col.startswith(Instr_level+'Interval') and 'Intervals' not in col and not col.endswith('Per') and 'Intervallic' not in col:
                intervals_list.append(col)
            elif 'Degree' in col and col.endswith('_Count'):
                degrees_list.append(col)
            elif 'Degree' in col and 'relative' in col and not 'Per' in col:
                degrees_relative_list.append(col)

        intervals_types_list.append(Instr_level + interval.constants.REPEATED_NOTES_COUNT)

        return intervals_list, intervals_types_list, degrees_list, degrees_relative_list

    def _find_melody_columns(self, all_info, catch):
        melody_values_list = get_melody_list(catch)
        if catch + lyrics.constants.SYLLABIC_RATIO in all_info.columns:
            melody_values_list.append(catch + lyrics.SYLLABIC_RATIO)
            
        melody_values=all_info[melody_values_list]  
        melody_values.columns = [c.replace(catch, '').replace('_Count', '')
                                for c in melody_values.columns]
        return melody_values

    def _find_interval_columns(self, all_info, catch, intervals_list, intervals_types_list):
        intervals_info=all_info[intervals_list]
        intervals_info.columns = [c.replace(catch+'Interval', '').replace('_Count', '')
                                    for c in intervals_info.columns]
        intervals_types=all_info[intervals_types_list]
        intervals_types.columns = [c.replace(catch, '').replace('Intervals', '').replace('_Count', '')
                                    for c in intervals_types.columns]
        return intervals_info, intervals_types

    def _get_instrument_prefix(self, instrument: list):
            if instrument.lower().startswith('vn'):  # Violins are the exception in which we don't take Sound level data
                prefix = 'Part'
            elif self._IsVoice(instrument):
                prefix = 'Family'
                instrument=VOICE_FAMILY.capitalize()
            else:
                prefix = 'Sound'
                instrument=instrument.replace('I','')
            
            inst=prefix+instrument
            return inst
    def _get_additional_info_and_groups(self, factor, rows_groups):
        additional_info = {ARIA_LABEL: [TITLE],
                                TITLE: [ARIA_LABEL]}

        if factor == 0:
            # rows_groups = {ARIA_ID: ([], "Alphabetic")}
            # rg_keys = [rows_groups[r][0] if rows_groups[r][0] != [] else r for r in rows_groups]
            rg_keys = list(rows_groups.keys())
            for r in rg_keys:
                if type(r) == list:
                    self.not_used_cols += r
                else:
                   self.not_used_cols.append(r)
            additional_info = [ARIA_LABEL, TITLE, COMPOSER, YEAR]
        rg_groups = [[]]
        if factor >= 2:
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
                                in list(self.metadata_columns)]
                            
        return additional_info,rg_groups

    def _tasks_execution(self, rg: dict, nuc:list, _cfg: Configuration, groups: list, additional_info, factor: int, common_columns_df: DataFrame, results_path:str=None, **kwargs): 
        global rows_groups
        global not_used_cols
        rows_groups=rg
        not_used_cols=nuc
        visualizations = True #remove with threads

        if results_path is None:
            results_path = self._rename_path(groups)

        if os.path.exists(path.join(results_path, 'visualisations')):
            remove_folder_contents(
                path.join(results_path, 'visualisations'))
        else:
            os.makedirs(path.join(results_path, 'visualisations'))

        # MUTITHREADING
        try:
            # executor = concurrent.futures.ThreadPoolExecutor()
            # visualizations = threading.Lock()
            # futures = []

            pre_string='-'.join(groups) + str(factor) + '_factor_'
            kwargs['common_df'] = common_columns_df

            if 'melody_values' in kwargs:
                # melody_values = pd.concat([common_columns_df,  kwargs["melody_values"]], axis=1)
                Melody_values(rows_groups, not_used_cols, factor, _cfg, kwargs, results_path, pre_string , "Melody_Values.xlsx",
                        self.visualizations, additional_info, True if factor == 0 else False, groups if groups != [] else None)
            if 'density' in kwargs:
                density_df = pd.concat(
                    [common_columns_df, kwargs["density"], kwargs["notes"]], axis=1)
                Densities(rows_groups, not_used_cols, factor, _cfg, density_df, results_path, pre_string, "Densities", self.visualizations, groups if groups != [] else None, additional_info)
            
            if 'textures' in kwargs:
                textures_df = pd.concat(
                [common_columns_df, kwargs["textures"], kwargs["notes"]], axis=1)
                Textures(rows_groups, not_used_cols, factor, _cfg, textures_df, results_path, pre_string, "Textures", self.visualizations, groups if groups != [] else None, additional_info)
            
            if 'intervals_info' in kwargs and not kwargs["intervals_info"].empty:
                intervals_info=pd.concat([common_columns_df, kwargs["intervals_info"]], axis=1)
                Intervals(rows_groups, not_used_cols, factor, _cfg, intervals_info, pre_string, "Intervals",
                                    _cfg.sorting_lists["Intervals"], results_path, self.visualizations, additional_info, groups if groups != [] else None)
                
                absolute_intervals=make_intervals_absolute(intervals_info)
                Intervals(rows_groups, not_used_cols, factor, _cfg, absolute_intervals, pre_string , "Intervals_absolute",
                                _cfg.sorting_lists["Intervals_absolute"], results_path, self.visualizations, additional_info, groups if groups != [] else None)
            
            if 'intervals_types' in kwargs:
                intervals_types = pd.concat([common_columns_df, kwargs["intervals_types"]], axis=1)
                Intervals_types(rows_groups, not_used_cols, factor, _cfg, intervals_types, results_path, pre_string, "Interval_types", self.visualizations, groups if groups != [] else None, additional_info)
            
            if 'scale' in kwargs and not kwargs['scale'].empty:
                emphasised_scale_degrees_info_A = pd.concat([common_columns_df,kwargs['scale']], axis=1)
                Emphasised_scale_degrees(rows_groups, not_used_cols, factor, _cfg, emphasised_scale_degrees_info_A, pre_string,  "Scale_degrees", results_path, self.visualizations, groups if groups != [] else None, additional_info)
            
            if 'scale_relative' in kwargs:
                emphasised_scale_degrees_info_B = pd.concat([common_columns_df,kwargs['scale_relative']], axis=1)
                Emphasised_scale_degrees(rows_groups, not_used_cols, factor, _cfg, emphasised_scale_degrees_info_B, pre_string, "Scale_degrees_relative", results_path, self.visualizations, groups if groups != [] else None, additional_info)
           
            if 'clefs' in kwargs:
                clefs_info= pd.concat([common_columns_df,kwargs['clefs']], axis=1)
                Intervals(rows_groups, not_used_cols, factor, _cfg, clefs_info, pre_string, "Clefs_in_voice",
                                _cfg.sorting_lists["Clefs"], results_path, self.visualizations, additional_info, groups if groups != [] else None)
            
            if 'harmonic_data' in kwargs:
                kwargs['common_df'] = common_columns_df
                Harmonic_analysis(rows_groups, not_used_cols, factor, _cfg, kwargs, pre_string, "Harmonic_Analysis", results_path, self.visualizations, additional_info, groups if groups != [] else None)

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
            lerr('An error ocurred during the report generation process.')
            sys.exit(2)

    def _rename_path(self, groups):
        if groups:
                # if sequential:
            results_path = path.join(self.results_path_factorx, '_'.join(groups))
            if not os.path.exists(results_path):
                os.mkdir(results_path)
        else:
            results_path = self.results_path_factorx
        return results_path

