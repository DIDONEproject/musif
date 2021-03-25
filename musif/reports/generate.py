########################################################################
# WRITE MODULE
########################################################################
# This script is ment to read the intermediate files computed by the
# read module and perform several computations while grouping the data
# based on several characteristics.
# Writes the final report files as well as generates the visualisations
########################################################################
import copy
import glob
import json
import math
import os
import shutil
import sys
import threading  # for the lock used for visualising, as matplotlib is not thread safe
from copy import deepcopy
from itertools import combinations, permutations
from os import path
from typing import List, Tuple

import numpy as np
import openpyxl
import pandas as pd
from music21 import interval, note, pitch
from musif.common.utils import read_object_from_yaml_file
from musif.config import Configuration
from pandas import DataFrame
# import concurrent
# from source.SortingGroupings import general_sorting, melody_sorting
from tqdm import tqdm

from .constants import not_used_cols, rows_groups
from .tasks import (IIIIntervals_types, emphasised_scale_degrees, iiaIntervals,
                    iValues, make_intervals_absolute)


class FeaturesGenerator():

    def __init__(self, *args, **kwargs):
        config_data = kwargs
        self._cfg = Configuration(**config_data)
        self.visualiser_lock = False

    def generate_reports(self, df: Tuple[DataFrame, DataFrame], num_factors: int = 0, main_results_path: str = '') -> DataFrame:
        self.global_features = df
        self.num_factors_max = num_factors
        self.main_results_path = main_results_path
        # self.parts_features = df[1]
        self.sorting_lists = self._read_sorting_lists()
        self._write(self.global_features)

    def _read_sorting_lists(self):
        return self._cfg.sorting_lists

    def _remove_folder_contents(self, path):
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                self._remove_folder_contents(file_path)

    def _write(self, all_dataframes: List[DataFrame]):
        # 2. rStart the factor generation
        for i in range(0, self.num_factors_max + 1):
            self._factor_execution(
                all_dataframes, i)

    def _factor_execution(self, all_dataframes, i):
        global rows_groups
        global not_used_cols

        main_results_path = os.path.join(self.main_results_path, 'results')
        rg = copy.deepcopy(rows_groups)
        nuc = copy.deepcopy(not_used_cols)

        # 1. Split all the dataframes to work individually
        common_columns = all_dataframes.iloc[:, 0:all_dataframes.columns.get_loc(
            'TempoGrouped2')]

        all_info = pd.concat(
            [common_columns, all_dataframes[['Intervalic ratio']]], axis=1)
        # intervals_info = pd.concat([common_columns, all_dataframes[['Intervalic ratio']], axis=1)
        # "IntervallicRatio": interval_ratio,
        # "TrimmedIntervallicRatio": trimmed_interval_ratio,
        # "TrimmedDiff": trim_diff,
        # "TrimRatio": trim_ratio,
        # "AbsoluteIntervallicRatio": absolute_interval_mean,
        # "Std": interval_std,
        # "AbsoluteStd": absolute_interval_std,
        # "AscendingSemitones": ascending_semitones,
        # "AscendingInterval": ascending_semitones_name,
        # "DescendingSemitones": descending_semitones,
        # "DescendingInterval": descending_semitones_name,
        # all_info, intervals_info, clefs_info, intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B = all_dataframes

        # all_info = all_info.dropna(how='all', axis=1)
        intervals_info = intervals_info.dropna(how='all', axis=1)
        # intervals_types = intervals_types.dropna(how='all', axis=1)
        # emphasised_scale_degrees_info_A = emphasised_scale_degrees_info_A.dropna(
        #     how='all', axis=1)
        # emphasised_scale_degrees_info_B = emphasised_scale_degrees_info_B.dropna(
        #     how='all', axis=1)
        # clefs_info = clefs_info.dropna(how='all', axis=1)
        # print(str(i) + " factor")

        # 2. Get the additional_info dictionary (special case if there're no factors)
        additional_info = {"Label": ["Aria"],
                           "Aria": ['Label']}  # solo agrupa aria
        if i == 0:
            rows_groups = {"Id": ([], "Alphabetic")}
            rg_keys = [rg[r][0] if rg[r][0] != [] else r for r in rg]
            for r in rg_keys:
                if type(r) == list:
                    not_used_cols += r
                else:
                    not_used_cols.append(r)
            # It a list, so it is applicable to all grouppings
            additional_info = ["Label", "Aria", "Composer", "Year"]

        rg_groups = [[]]
        if i >= 2:
            rg_groups = list(permutations(
                list(forbiden_groups.keys()), i - 1))[4:]

            if i > 2:
                prohibidas = ['Composer', 'Opera']
                for g in rg_groups:
                    if 'Aria' in g:
                        g_rest = g[g.index('Aria'):]
                        if any(p in g_rest for p in prohibidas):
                            rg_groups.remove(g)
                    elif 'Label' in g:
                        g_rest = g[g.index('Label'):]
                        if any(p in g_rest for p in prohibidas):
                            rg_groups.remove(g)
            rg_groups = [r for r in rg_groups if r[0]
                         in list(all_info.columns)]

        results_path_factorx = path.join(main_results_path, str(
            i) + " factor") if i > 0 else path.join(main_results_path, "Data")
        if not os.path.exists(results_path_factorx):
            os.mkdir(results_path_factorx)

        absolute_intervals = make_intervals_absolute(intervals_info)

        # # MULTIPROCESSING (one process per group (year, decade, city, country...))
        # if sequential: # 0 and 1 factors
        for groups in rg_groups:
            self._group_execution(groups, results_path_factorx, additional_info, i, self.sorting_lists, all_info, intervals_info, absolute_intervals,
                                  intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info)
            rows_groups = rg
            not_used_cols = nuc
        # else: # from 2 factors
        #     # process_executor = concurrent.futures.ProcessPoolExecutor()
        #     futures = [process_executor.submit(self._group_execution, groups, results_path_factorx, additional_info, i, sorting_lists, all_info, intervals_info, absolute_intervals, intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info, sequential) for groups in rg_groups]
        #     kwargs = {'total': len(futures),'unit': 'it','unit_scale': True,'leave': True}
        #     for f in tqdm(concurrent.futures.as_completed(futures), **kwargs):
        #         rows_groups = rg
        #         not_used_cols = nuc

    #####################################################################
    # Function that generates the needed information for each grouping  #
    #####################################################################
    def _group_execution(self, groups, results_path_factorx, additional_info, i, sorting_lists, all_info, intervals_info, absolute_intervals, intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info):
        if groups:
            # if sequential:
            results_path = path.join(results_path_factorx, '_'.join(groups))
            if not os.path.exists(results_path):
                os.mkdir(results_path)
        else:
            results_path = results_path_factorx
        if os.path.exists(path.join(results_path, 'visualisations')):
            self._remove_folder_contents(
                path.join(results_path, 'visualisations'))
        else:
            os.mkdir(path.join(results_path, 'visualisations'))
        # MUTITHREADING
        try:
            # executor = concurrent.futures.ThreadPoolExecutor()
            # self.visualiser_lock = threading.Lock()
            # futures = []
            if not all_info.empty:
                # futures.append(executor.submit(iValues, all_info, results_path, '-'.join(groups) + "_1Values.xlsx", sorting_lists,
                #                self.visualiser_lock, additional_info, True if i == 0 else False, groups if groups != [] else None))
                iValues(all_info, results_path, '-'.join(groups) + "_1Values.xlsx", sorting_lists,
                        self.visualiser_lock, additional_info, True if i == 0 else False, groups if groups != [] else None)
                # if not intervals_info.empty:
                #     futures.append(executor.submit(iiaIntervals, intervals_info, '-'.join(groups) + "_2aIntervals.xlsx",
                #                    sorting_lists["Intervals"], results_path, sorting_lists, self.visualiser_lock, additional_info, groups if groups != [] else None))
                #     futures.append(executor.submit(iiaIntervals, absolute_intervals, '-'.join(groups) + "_2bIntervals_absolute.xlsx",
                #                    sorting_lists["Intervals_absolute"], results_path, sorting_lists, self.visualiser_lock, additional_info, groups if groups != [] else None))
                # if not intervals_types.empty:
                #     futures.append(executor.submit(IIIIntervals_types, intervals_types, results_path, '-'.join(groups) +
                #                    "_3Interval_types.xlsx", sorting_lists, self.visualiser_lock, groups if groups != [] else None, additional_info))
                # if not emphasised_scale_degrees_info_A.empty:
                #     futures.append(executor.submit(emphasised_scale_degrees, emphasised_scale_degrees_info_A, sorting_lists["ScaleDegrees"], '-'.join(
                #         groups) + "_4aScale_degrees.xlsx", results_path, sorting_lists, self.visualiser_lock, groups if groups != [] else None, additional_info))
                # if not emphasised_scale_degrees_info_B.empty:
                #     futures.append(executor.submit(emphasised_scale_degrees, emphasised_scale_degrees_info_B, sorting_lists["ScaleDegrees"], '-'.join(
                #         groups) + "_4bScale_degrees_relative.xlsx", results_path, sorting_lists, self.visualiser_lock, groups if groups != [] else None, additional_info))
                # if not clefs_info.empty:
                #     futures.append(executor.submit(iiaIntervals, clefs_info, '-'.join(groups) + "_5Clefs.xlsx",
                #                    sorting_lists["Clefs"], results_path, sorting_lists, self.visualiser_lock, additional_info, groups if groups != [] else None))

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
            sys.exit(2)
        except Exception as e:
            pass
