import os
import sys
from os import path

import musif.extract.features.ambitus as ambitus
import musif.extract.features.lyrics as lyrics
import numpy as np
import pandas as pd
from config import Configuration
from musif.common.constants import RESET_SEQ
from pandas.core.frame import DataFrame

from .calculations import make_intervals_absolute
from .constants import *
from .tasks.melody_values import Melody_values
from .tasks.intervals import Intervals, Intervals_types
from .tasks.scale_degrees import Emphasised_scale_degrees
from .tasks.common_tasks import Densities, Textures
from .tasks.harmony import Harmonic_data, Keyareas_columns, Keyareas, Keyareas_weighted, Chords, Harmonic_functions

from musif.reports.utils import remove_folder_contents

#Initialize global config vaiable
cgf=None
rows_groups={}
not_used_cols={}

if not os.path.exists(path.join(os.getcwd(), 'logs')):
    os.mkdir(path.join(os.getcwd(), 'logs'))

#####################################################################

def _tasks_execution(rg: dict, nuc:list, _cfg: Configuration, groups: list, results_path_factorx: str, additional_info, factor: int, common_columns_df: DataFrame, 
notes_df: DataFrame = pd.DataFrame(), melody_values: DataFrame = pd.DataFrame(), density_df: DataFrame =pd.DataFrame(), textures_df: DataFrame =pd.DataFrame(),
intervals_info: DataFrame = pd.DataFrame(),intervals_types: DataFrame =pd.DataFrame(), clefs_info: DataFrame =pd.DataFrame(), emphasised_scale_degrees_info_A: DataFrame =pd.DataFrame(),
harmony_df: DataFrame = pd.DataFrame(), key_areas: DataFrame = pd.DataFrame(), chords: DataFrame = pd.DataFrame(), functions: DataFrame = pd.DataFrame()):
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
        if not melody_values.empty:
            #     # futures.append(executor.submit(Melody_values, Melody_values, results_path, '-'.join(groups) + "_1Values.xlsx", sorting_lists,
            #     #                visualiser_lock, additional_info, True if i == 0 else False, groups if groups != [] else None))
            melody_values = pd.concat([common_columns_df, melody_values], axis=1)
            Melody_values(rows_groups, not_used_cols, factor, _cfg, melody_values, results_path, pre_string + "Melody_Values.xlsx",
                    visualiser_lock, additional_info, True if factor == 0 else False, groups if groups != [] else None)
        if not density_df.empty:
            density_df = pd.concat(
                [common_columns_df, density_df,notes_df], axis=1)
            Densities(rows_groups, not_used_cols, factor, _cfg, density_df, results_path, pre_string+  "Densities.xlsx", visualiser_lock, groups if groups != [] else None, additional_info)
        if not textures_df.empty:
            textures_df = pd.concat(
            [common_columns_df, textures_df,notes_df], axis=1)
            Textures(rows_groups, not_used_cols, factor, _cfg, textures_df, results_path, pre_string + "Textures.xlsx", visualiser_lock, groups if groups != [] else None, additional_info)
        if not intervals_info.empty:
            intervals_info=pd.concat([common_columns_df, intervals_info], axis=1)
            Intervals(rows_groups, not_used_cols, factor, _cfg, intervals_info, pre_string+ "Intervals.xlsx",
                                _cfg.sorting_lists["Intervals"], results_path, visualiser_lock, additional_info, groups if groups != [] else None)
            
            absolute_intervals=make_intervals_absolute(intervals_info)
            Intervals(rows_groups, not_used_cols, factor, _cfg, absolute_intervals, pre_string + "Intervals_absolute.xlsx",
                            _cfg.sorting_lists["Intervals_absolute"], results_path, visualiser_lock, additional_info, groups if groups != [] else None)
        if not intervals_types.empty:
            intervals_types = pd.concat([common_columns_df, intervals_types], axis=1)
            Intervals_types(rows_groups, not_used_cols, factor, _cfg, intervals_types, results_path, pre_string + "Interval_types.xlsx", visualiser_lock, groups if groups != [] else None, additional_info)
        
        if not emphasised_scale_degrees_info_A.empty:
            emphasised_scale_degrees_info_A = pd.concat([common_columns_df,emphasised_scale_degrees_info_A], axis=1)
            Emphasised_scale_degrees(rows_groups, not_used_cols, factor, _cfg, emphasised_scale_degrees_info_A,  _cfg.sorting_lists["ScaleDegrees"], pre_string +  "Scale_degrees.xlsx", results_path, visualiser_lock, groups if groups != [] else None, additional_info)
        # if not Emphasised_scale_degrees_info_B.empty:
        #     Emphasised_scale_degrees( Emphasised_scale_degrees_info_B, sorting_lists["ScaleDegrees"], '-'.join(
        #         groups) + "_4bScale_degrees_relative.xlsx", results_path, sorting_lists, visualiser_lock, groups if groups != [] else None, additional_info)
        if not clefs_info.empty:
            clefs_info= pd.concat([common_columns_df,clefs_info], axis=1)
            Intervals(rows_groups, not_used_cols, factor, _cfg, clefs_info, pre_string +  "Clefs_in_voice.xlsx",
                            _cfg.sorting_lists["Clefs"], results_path, visualiser_lock, additional_info, groups if groups != [] else None)
        if not harmony_df.empty:
            harmony_df= pd.concat([common_columns_df,harmony_df], axis=1)
            # Harmonic_data(rows_groups, not_used_cols, factor, cfg, harmony_df, '-'.join(groups) + "Harmonic_rythm.xlsx",
            #                 sorting_lists["Clefs"], results_path, sorting_lists, visualiser_lock, additional_info, groups if groups != [] else None)
        if not chords.empty:
            chords = pd.concat([common_columns_df, chords], axis=1)
            Chords(rows_groups, not_used_cols, factor, _cfg, chords, results_path, pre_string+  "Chords.xlsx", visualiser_lock, groups if groups != [] else None, additional_info)
        if not functions.empty:
            functions = pd.concat([common_columns_df, functions], axis=1)
            Harmonic_functions(rows_groups, not_used_cols, factor, _cfg, functions, results_path, pre_string+  "Harmonic_functions.xlsx", visualiser_lock, groups if groups != [] else None, additional_info)
       
        # if not key_areas.empty:
        #     key_areas= pd.concat([common_columns_df,key_areas], axis=1)
        #     # clefs_info= pd.concat([common_columns_df,clefs_info], axis=1)
        #     Keyareas(cfg, key_areas, results_path, '-'.join(groups) + "_Key_areas.xlsx",
        #                 sorting_lists, visualiser_lock, groups if groups != [] else None, additional_info)
        #     Keyareas_weigthed(cfg, key_areas, results_path, '-'.join(groups) + "_Key_areas.xlsx",
        #                 sorting_lists, visualiser_lock, groups if groups != [] else None, additional_info)
            
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
        _cfg.write_logger.error('\033[93mAn error ocurred during the report generation process. \033[37m')
        sys.exit(2)

