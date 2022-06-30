import copy
import os
import sys
from itertools import permutations
from os import path
from typing import Dict, List, Set, Tuple
from musif.process.utils import merge_single_voices

import pandas as pd
from musif.common.constants import LEVEL_DEBUG, LEVEL_ERROR
from musif.common._utils import colorize
from musif.config import Configuration
from musif.extract.constants import VOICES_LIST
from musif.extract.features import (density, harmony, lyrics, scale,
                                    scale_relative, texture)
from musif.extract.features.harmony.constants import (KEY_GROUPING, KEY_PREFIX,
                                                      ADDITIONS_prefix,
                                                      CHORD_prefix,
                                                      CHORD_TYPES_prefix,
                                                      CHORDS_GROUPING_prefix,
                                                      HARMONIC_prefix,
                                                      NUMERALS_prefix)
from musif.extract.features.tempo.constants import NUMBER_OF_BEATS
from musif.logs import lerr, perr
# from musif.process.utils import merge_single_voices
from musif.reports.calculations import make_intervals_absolute
from musif.reports.utils import capitalize_instruments, remove_folder_contents
from pandas import DataFrame
from tqdm import tqdm

from ..logs import pinfo
from .constants import *
from .tasks.common_tasks import Densities, Textures
from .tasks.harmony import Harmonic_analysis
from .tasks.intervals import Intervals, Intervals_types
from .tasks.melody_values import melody_values
from .tasks.scale_degrees import Emphasised_scale_degrees


class ReportsGenerator:
    """
    Collects data from a Dataframe generated by FeaturesExtrator and generates several
    excel files that present the information grouping by different categories and creates
    visualizations to understand better the data.
        
    ...

    Attributes
    ----------
    self.all_info : DataFrame
        DataFrame extracted with FeaturesExtractor containing all info.

    Methods
    -------
    generate_reports(self, data: DataFrame, main_results_path: str, num_factors: int = 0, visualizations: bool = False)
        Processes DataFrame information and generates different reports according to the introduced parameters 
    """

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args:  Could be a path to a .yml file, a Configuration object or a dictionary. Length zero or one.
        **kwargs: Get keywords to construct Configuration.

        Raises
        ------
        TypeError
         - If the type is not the expected (str, dict or Configuration).
        ValueError
          - If there is too many arguments(args)
        FileNotFoundError
          - If any of the files/directories path inside the expected configuration doesn't exit.
        """
        self._cfg = Configuration(*args, **kwargs)

    def generate_reports(self, data: DataFrame, main_results_path: str, num_factors: int = 0, visualizations: bool = False) -> None:
        """
        Generates reports files in .xlsx format given a DataFrame object previously generated
        by FeaturesExractor. By using different parameters and the configuration file,
        reports can be customized for user's preference.  
        
        Parameters
        ------
        main_results_path: str
            Route to the folder where the reports will be stored.
        num_factors: int
            Max num of factor generation. 0 will not group scores apart from basic metadata, 
            1 will create different groups for every possible grouping key (Opera, Location, AriaId, Key, etc.)
            2 or more will create different folders with subdivision (high computational cost!) 
        visualizations: bool
            Whether visualizations of the reports are to be generated or not.   

        """
        pinfo('\n'+'--- Starting reports generation ---\n'.center(120, ' '))
        self.parts_list = [] if self._cfg.parts_filter is None else self._cfg.parts_filter
        self.visualizations = visualizations
        pinfo(colorize('Visualizations are enabled', LEVEL_DEBUG) if self.visualizations else colorize('Visualizations are disabled', LEVEL_ERROR)+'.\n')
        
        self.all_info = data
        self.num_factors_max = num_factors
        self.main_results_path = os.path.join(main_results_path, 'results')
        self.sorting_lists = self._cfg.sorting_lists
        self._write()

    def _write(self) -> None:
        for factor in range(0, self.num_factors_max + 1):
            self._factor_execution(factor)
           
    def _factor_execution(self, num_factors: int = 0) -> None:
        global rows_groups
        global not_used_cols
        self.not_used_cols = not_used_cols
        self.rows_groups = rows_groups
        self.not_used_cols_original = not_used_cols
        self.rows_groups_original = rows_groups

        self.metadata_columns=metadata_columns
        
        common_columns_df = self._find_common_columns()

        pinfo('\n' + str(num_factors) + " factor" + "\n")
        instruments = self._extract_instruments()
        merge_single_voices(self.all_info)
        

        common_tasks, harmony_tasks=self._prepare_common_dataframes(instruments)

        additional_info, rg_groups = self._get_additional_info_and_groups(num_factors) 

        self._run_common_tasks(num_factors, common_columns_df, common_tasks, harmony_tasks, additional_info, rg_groups)
        self._run_tasks_per_instrument(instruments, common_columns_df, num_factors, rg_groups, additional_info)
        

        
    def _find_common_columns(self) -> DataFrame:
        common_columns_df= pd.DataFrame()
        columns_to_remove=[]
        for column in self.metadata_columns:
            info=self.all_info.get(column)
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

    def _find_notes_set(self, instruments: List[str]) -> Set[str]:
        notes_set=set([])
        for instrument in instruments:
            if instrument.lower().startswith('vn'):
                notes_set.add(self._get_instrument_prefix(instrument) + '_Notes')
            else:
                notes_set.add(self._get_instrument_prefix(instrument) + '_NotesMean')
        return notes_set

    def _prepare_part_dataframes(self, common_columns_df: DataFrame, tasks: list, instrument_level: str, instrument: str) -> None:
        intervals_list, intervals_types_list, degrees_list, degrees_relative_list = self._find_interval_degree_columns(instrument_level)
        
        if self._cfg.is_requested_module(interval):            
            intervals_info, intervals_types = self._find_interval_columns(instrument_level, intervals_list, intervals_types_list)
            intervals_info.dropna(how='all', axis=1, inplace=True)
            intervals_types.dropna(how='all', axis=1, inplace=True)
            if not intervals_info.empty:
                tasks['intervals_info'] = intervals_info
            if not intervals_types.empty:
                tasks['intervals_types'] = intervals_types

        if self._cfg.is_requested_module(ambitus):      
            try:     
                if not self._cfg.is_requested_module(interval):
                    perr('Interval module is needed to generate Melody values report!')
                    tasks['melody_values']=pd.DataFrame()
                else:
                    tasks['melody_values'] = self._find_melody_columns(instrument_level).dropna(how='all', axis=1)
            except KeyError as e:                 
                perr('Melody Values information could not be extracted'.format(e))

        if instrument=='Voice':
            if self._cfg.is_requested_module(scale):            
                tasks['scale'] = self._find_scale_degrees_columns(instrument_level, degrees_list).dropna(how='all', axis=1)
            if self._cfg.is_requested_module(scale_relative):            
                tasks['scale_relative'] = self._find_scale_degrees_columns(instrument_level, degrees_relative_list).dropna(how='all', axis=1)
            tasks['clefs'] = self._get_clefs(common_columns_df)

    def _prepare_common_dataframes(self, instruments: List[str]) -> Tuple[Dict, Dict]:
        common_tasks={}
        harmony_tasks={}
        if self._cfg.is_requested_module(density) or self._cfg.is_requested_module(texture):
            notes_set = self._find_notes_set(instruments)    
            notes_df=self.all_info[list(notes_set)]
            common_tasks['notes']=notes_df
        
        if self._cfg.is_requested_module(density):
            density_df = self._find_density_columns(instruments)
            common_tasks['density']=density_df

        if self._cfg.is_requested_module(texture):
            textures_df = self.all_info[[i for i in self.all_info.columns if i.endswith('Texture')]].copy()
            common_tasks['textures'] = textures_df

        if self._cfg.is_requested_module(harmony):
            harmony_df, key_areas_df, chords_df, functions_dfs = self._find_harmony_columns()
            harmony_tasks['harmonic_data']=harmony_df
            harmony_tasks['key_areas']=key_areas_df
            harmony_tasks['chords']=chords_df
            harmony_tasks['functions']=functions_dfs
        
        return common_tasks, harmony_tasks

    def _run_common_tasks(self, factor: int, common_columns_df: DataFrame, common_tasks: Dict[str, str], harmony_tasks: Dict[str, str], additional_info: Dict[str, str], rg_groups: Dict[str, str]) -> None:
        pinfo('\n'+'--- Generating common reports: Density, Texture and Harmony ---'.center(120))

        for groups in rg_groups:
            
            if self._cfg.is_requested_module(texture) or self._cfg.is_requested_module(density):
                textures_densities_data_path = path.join(self.main_results_path, 'Texture&Density', str(
                        factor) + " factor") if factor > 0 else path.join(self.main_results_path, 'Texture&Density', "Data")
                if not os.path.exists(textures_densities_data_path):
                    os.makedirs(textures_densities_data_path)

                self._tasks_execution(self._cfg,
                            groups, additional_info, factor, common_columns_df,results_path= textures_densities_data_path, **common_tasks)
            
            if self._cfg.is_requested_module(harmony):
                harmony_data_path = path.join(self.main_results_path, 'Harmony', str(
                            factor) + " factor") if factor > 0 else path.join(self.main_results_path, 'Harmony', "Data")
                if not os.path.exists(harmony_data_path):
                     os.makedirs(harmony_data_path)

                self._tasks_execution(self._cfg,
                             groups, additional_info, factor, common_columns_df,results_path=harmony_data_path, **harmony_tasks)

    def _run_tasks_per_instrument(self, instruments: list, common_columns_df: DataFrame, num_factors: int, rg_groups: dict, additional_info: dict) -> None:
        pinfo('\n'+'--- Generating reports per instrument ---'.center(120))
        
        for instrument in tqdm(list(instruments)):
            tasks={}

            pinfo(f'\nGenerating reports for instrument:\t{instrument}' + '\n')

            instrument_level = 'Part' + instrument + '_'
            
            if instrument=='Voice':
                instrument_level = 'Sound' + instrument + '_'

            
            self._prepare_part_dataframes(common_columns_df, tasks, instrument_level, instrument)
            
            self.results_path_factorx = path.join(self.main_results_path, 'Melody_' + instrument, str(
                num_factors) + " factor") if num_factors > 0 else path.join(self.main_results_path,'Melody_'+ instrument, "Data")
            if not os.path.exists(self.results_path_factorx):
                os.makedirs(self.results_path_factorx)

            # if sequential: # 0 and 1 factors
            for groups in rg_groups:
                try:
                    self._tasks_execution(self._cfg, 
                        groups, additional_info, num_factors, common_columns_df, **tasks)
                    # self.rows_groups = rg
                    # self.not_used_cols = nuc
                except KeyError as e:
                    perr('One or more of the features could not be found in the input dataframe: '.format(e))
                # else: # from 2 factors
                    # process_executor = concurrent.futures.ProcessPoolExecutor()
                    # futures = [process_executor.submit(_group_execution, groups, results_path_factorx, additional_info, i, sorting_lists, Melody_values, intervals_info, absolute_intervals, Intervals_types, Emphasised_scale_degrees_info_A, Emphasised_scale_degrees_info_B, clefs_info, sequential) for groups in rg_groups]
                    # kwargs = {'total': len(futures),'unit': 'it','unit_scale': True,'leave': True}
                    # for f in tqdm(concurrent.futures.as_completed(futures), **kwargs):
                    #     rows_groups = rg
                    #     not_used_cols = nuc

    def _get_clefs(self, common_columns_df: DataFrame) -> DataFrame:
        if ('Clef2' and 'Clef3') in common_columns_df.columns:
            common_columns_df.Clef2.replace('', 'NA', inplace=True)
            common_columns_df.Clef3.replace('', 'NA', inplace=True)
        clefs_info=copy.deepcopy(common_columns_df)
        clefs_set = set([str(self.all_info['Clef1'][0]),str(self.all_info['Clef2'][0]), str(self.all_info['Clef3'][0])])
        if 'nan' in clefs_set:
            clefs_set.remove('nan')
        for clef in clefs_set:
            clefs_info[clef] = 0
            for r, j in enumerate(clefs_info.iterrows()):
                clefs_info[clef].iloc[r] = float(len([i for i in clefs_info[['Clef1','Clef2','Clef3']].iloc[r] if i == clef]))
        clefs_info.replace('', 'NA', inplace=True)
        clefs_info.dropna(how='all', axis=1, inplace=True)
        return clefs_info

    def _extract_instruments(self) -> Set[str]:
        instruments = set([])
        all_instruments = set([inst for aria in self.all_info['Scoring'] for inst in aria.split(',')])
        
        if self.parts_list:
            for inst in self.parts_list:
                if inst in all_instruments:
                    instruments.add(inst)
        else:
            instruments = all_instruments

        for inst in instruments.copy():
            if inst in VOICES_LIST:
                instruments.add('voice')
                instruments.remove(inst)
            
        instruments = capitalize_instruments(instruments)
        return instruments

    def _find_density_columns(self, instruments):
        density_set = set([])
        for instrument in instruments:
            density_set.add(
                    self._get_instrument_prefix(instrument)  + '_SoundingDensity')
            density_set.add(
                    self._get_instrument_prefix(instrument)  + '_SoundingMeasures')
            if instrument.endswith('II'):
                continue
        density_set.add(NUMBER_OF_BEATS)
        density_df = self.all_info[list(density_set)]
        return density_df

    def _find_harmony_columns(self):
        harmony_df=self.all_info[(
            [i for i in self.all_info.columns if HARMONIC_prefix in i] +
            [i for i in self.all_info.columns if CHORD_TYPES_prefix in i] +
            [i for i in self.all_info.columns if ADDITIONS_prefix in i]
            )]
        key_areas_df=self.all_info[[i for i in self.all_info.columns if KEY_PREFIX in i or KEY_GROUPING in i ]]
        functions_dfs = self.all_info[[i for i in self.all_info.columns if NUMERALS_prefix in i and i.endswith('_Count')] + [i for i in self.all_info.columns if CHORDS_GROUPING_prefix in i and i.endswith('_Count')]]
        chords_df = self.all_info[[i for i in self.all_info.columns if CHORD_prefix in i and CHORD_TYPES_prefix not in i and i.endswith('_Count')]]
        return harmony_df,key_areas_df,chords_df,functions_dfs

    def _find_scale_degrees_columns(self, catch, degrees_list):
        scale_degrees_info=self.all_info[[c for c in degrees_list if catch in c]]
        scale_degrees_info.columns = [c.replace(catch, '').replace('Degree', '').replace('_Count', '') for c in scale_degrees_info.columns]
        return scale_degrees_info

    def _find_interval_degree_columns(self, Instr_level):
        intervals_list = []
        intervals_types_list = []
        degrees_list = []
        degrees_relative_list = []

        for col in self.all_info.columns.values:
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

    def _find_melody_columns(self, catch):
        melody_values_list = get_melody_list(catch)
        if catch + lyrics.constants.SYLLABIC_RATIO in self.all_info.columns:
            melody_values_list.append(catch + lyrics.SYLLABIC_RATIO)
            
        melody_values=self.all_info[melody_values_list]  
        melody_values.columns = [c.replace(catch, '').replace('_Count', '')
                                for c in melody_values.columns]
        return melody_values

    def _find_interval_columns(self, catch, intervals_list, intervals_types_list):
        intervals_info=self.all_info[intervals_list]
        intervals_info.columns = [c.replace(catch+'Interval', '').replace('_Count', '')
                                    for c in intervals_info.columns]
        intervals_types=self.all_info[intervals_types_list]
        intervals_types.columns = [c.replace(catch, '').replace('Intervals', '').replace('_Count', '')
                                    for c in intervals_types.columns]
        return intervals_info, intervals_types

    def _get_instrument_prefix(self, instrument: list):
            if instrument.lower().startswith('vn'):  # Violins are the exception in which we don't take Sound level data
                prefix = 'Part'
            elif instrument=='Voice':  
                return 'Family'+instrument
            else:
                prefix = 'Sound'
                instrument=instrument.replace('I','')
            return prefix+instrument

    def _get_additional_info_and_groups(self, factor: int) -> Dict[str, str]:
        additional_info = {ARIA_LABEL: [TITLE],
                                TITLE: [ARIA_LABEL]}

        if factor == 0:
            self.rows_groups = {ARIA_ID: ([], "Alphabetic")}

            rg_keys = [self.rows_groups_original[r][0] if self.rows_groups_original[r][0] != [] else r for r in self.rows_groups_original]

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
                            
        return additional_info, rg_groups

    def _tasks_execution(self, _cfg: Configuration, groups: list, additional_info, factor: int, common_columns_df: DataFrame, results_path:str=None, **kwargs): 
        # global rows_groups
        # global not_used_cols
        # rows_groups=rgdr
        
        if results_path is None:
            results_path = self._rename_path(groups)

        if self.visualizations: 
            if os.path.exists(path.join(results_path, VISUALIZATIONS)):
                remove_folder_contents(
                    path.join(results_path, VISUALIZATIONS))
            else:
                os.makedirs(path.join(results_path, VISUALIZATIONS))

        try:
            # executor = concurrent.futures.ThreadPoolExecutor()
            # visualizations = threading.Lock()
            # futures = []

            pre_string='-'.join(groups) + str(factor) + '_factor_'
            kwargs['common_df'] = common_columns_df

            if 'melody_values' in kwargs:
                melody_values(self.rows_groups, self.not_used_cols, factor, _cfg, kwargs, results_path, pre_string , "Melody_Values",
                        self.visualizations, additional_info, True if factor == 0 else False, groups if groups != [] else None)
            
            if 'density' in kwargs:
                density_df = pd.concat(
                    [common_columns_df, kwargs["density"], kwargs["notes"]], axis=1)
                Densities(self.rows_groups, self.not_used_cols, factor, _cfg, density_df, results_path, pre_string, "Densities", self.visualizations, groups if groups != [] else None, additional_info)
            
            if 'textures' in kwargs:
                textures_df = pd.concat(
                [common_columns_df, kwargs["textures"], kwargs["notes"]], axis=1)
                Textures(self.rows_groups, self.not_used_cols, factor, _cfg, textures_df, results_path, pre_string, "Textures", self.visualizations, groups if groups != [] else None, additional_info)
            
            if 'intervals_info' in kwargs and not kwargs["intervals_info"].empty:
                intervals_info=pd.concat([common_columns_df, kwargs["intervals_info"]], axis=1)
                Intervals(self.rows_groups, self.not_used_cols, factor, _cfg, intervals_info, pre_string, "Intervals",
                                    _cfg.sorting_lists["Intervals"], results_path, self.visualizations, additional_info, groups if groups != [] else None)
                
                absolute_intervals=make_intervals_absolute(intervals_info)
                Intervals(self.rows_groups, self.not_used_cols, factor, _cfg, absolute_intervals, pre_string , "Intervals_absolute",
                                _cfg.sorting_lists["Intervals_absolute"], results_path, self.visualizations, additional_info, groups if groups != [] else None)
            
            if 'intervals_types' in kwargs:
                intervals_types = pd.concat([common_columns_df, kwargs["intervals_types"]], axis=1)
                Intervals_types(self.rows_groups, self.not_used_cols, factor, _cfg, intervals_types, results_path, pre_string, "Interval_types", self.visualizations, groups if groups != [] else None, additional_info)
            
            if 'scale' in kwargs and not kwargs['scale'].empty:
                emphasised_scale_degrees_info_A = pd.concat([common_columns_df,kwargs['scale']], axis=1)
                Emphasised_scale_degrees(self.rows_groups, self.not_used_cols, factor, _cfg, emphasised_scale_degrees_info_A, pre_string,  "Scale_degrees", results_path, self.visualizations, groups if groups != [] else None, additional_info)
            
            if 'scale_relative' in kwargs:
                emphasised_scale_degrees_info_B = pd.concat([common_columns_df,kwargs['scale_relative']], axis=1)
                Emphasised_scale_degrees(self.rows_groups, self.not_used_cols, factor, _cfg, emphasised_scale_degrees_info_B, pre_string, "Scale_degrees_relative", results_path, self.visualizations, groups if groups != [] else None, additional_info)
           
            if 'clefs' in kwargs:
                # clefs_info = pd.concat([common_columns_df,kwargs['clefs']], axis=1)
                clefs_info = kwargs['clefs']
                Intervals(self.rows_groups, self.not_used_cols, factor, _cfg, clefs_info, pre_string, "Clefs_in_voice",
                                _cfg.sorting_lists["Clefs"], results_path, self.visualizations, additional_info, groups if groups != [] else None)
            
            if 'harmonic_data' in kwargs:
                kwargs['common_df'] = common_columns_df
                Harmonic_analysis(self.rows_groups, self.not_used_cols, factor, _cfg, kwargs, pre_string, "Harmonic_Analysis", results_path, self.visualizations, additional_info, groups if groups != [] else None)

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

    def _rename_path(self, groups: bool) -> str:
        if groups:
            results_path = path.join(self.results_path_factorx, '_'.join(groups))
            if not os.path.exists(results_path):
                os.mkdir(results_path)
        else:
            results_path = self.results_path_factorx
        return results_path

