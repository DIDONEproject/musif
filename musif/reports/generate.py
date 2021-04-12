########################################################################
# GENERATION MODULE
########################################################################
# This script is ment to read the intermediate DataFrame computed by the
# FeaturesExtractor and perform several computations while grouping the data
# based on several characteristics.
# Writes the final report files as well as generates the visualisations
########################################################################
import copy
from genericpath import exists
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
from typing import List, Tuple, Optional

import numpy as np
import openpyxl
import pandas as pd
from music21 import interval, note, pitch
from musif.common.utils import read_object_from_yaml_file
from musif.config import Configuration
from pandas import DataFrame
from tqdm import tqdm

from .constants import not_used_cols, rows_groups, metadata_columns, forbiden_groups
from .tasks import (IIIIntervals_types, emphasised_scale_degrees, iiaIntervals,
                    iValues, make_intervals_absolute, densities, textures)
import musif.extract.features.ambitus as ambitus


class FeaturesGenerator():

    def __init__(self, *args, **kwargs):
        config_data = kwargs
        self._cfg = Configuration(**config_data)
        self.visualiser_lock = True

    def generate_reports(self, df: Tuple[DataFrame, DataFrame], num_factors: int = 0, main_results_path: str = '', parts_list: Optional[List[str]] = None) -> DataFrame:
        self.parts_list = [] if parts_list is None else parts_list
        self.global_features = df
        self.num_factors_max = num_factors
        self.main_results_path = main_results_path
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
        common_columns_df = all_dataframes[metadata_columns]
        common_columns_df['Total analysed'] = 1.0
        all_info_list = []
        # all_info_list = ['ScoreSyllabicRatio', 'ScoreIntervallicMean', 'ScoreIntervallicStd', 'ScoreAbsoluteIntervallicMean', 'ScoreAbsoluteIntervallicStd', 'ScoreTrimmedAbsoluteIntervallicRatio',
        #                  'ScoreAbsoluteIntervallicTrimDiff', 'ScoreAbsoluteIntervallicTrimRatio', 'ScoreAscendingSemitones', 'ScoreAscendingInterval', 'ScoreDescendingSemitones', 'ScoreDescendingInterval', ambitus.LOWEST_NOTE]

        '''
        'Intervallic ratio',
       'Trimmed intervallic ratio', 'dif. Trimmed', '% Trimmed',
       'Absolute intervallic ratio', 'Std', 'Absolute Std', 'Syllabic ratio',
       'LowestNote', 'HighestNote', 'LowestIndex', 'HighestIndex',
       'LowestMeanNote', 'LowestMeanIndex', 'HighestMeanNote',
       'HighestMeanIndex', 'AmbitusLargestInterval', 'AmbitusLargestSemitones',
       'AmbitusSmallestInterval', 'AmbitusSmallestSemitones',
       'AmbitusAbsoluteInterval', 'AmbitusAbsoluteSemitones',
       'AmbitusMeanInterval', 'AmbitusMeanSemitones', 'AscendingSemitones',
       'AscendingInterval', 'DescendingSemitones', 'DescendingInterval'],
       '''

        clefs_info_list = ['Clef1']
        textures_list = []
        density_list = []

        instruments = set([])
        if self.parts_list:
            instruments = self.parts_list
        else:
            for aria in all_dataframes['Scoring']:
                for a in aria.split(','):
                    instruments.add(a)

        instruments = [instrument[0].upper()+instrument[1:]
                       for instrument in instruments]

        # FIltering columns for each feature
        for instrument in instruments:
            # ['sop', 'ten', 'alt', 'mez']:
            if instrument.lower().startswith('vn'):
                catch = 'Part'
            else:
                catch = 'Sound'
                if instrument.endswith('II'):
                    continue
                instrument = instrument.replace('I', '')
            # Capitalize does not work beacuse of violins being VnII, etc.
            density_list.append(
                catch + instrument + 'Notes')
            density_list.append(
                catch + instrument + 'SoundingDensity')
            density_list.append(
                catch + instrument + 'SoundingMeasures')
            textures_list.append(
                catch + instrument + 'Notes')
            textures_list.append(
                catch + instrument + 'Texture')

        all_info = pd.concat(
            [common_columns_df, all_dataframes[all_info_list]], axis=1)

        all_info = all_info.dropna(how='all', axis=1)
        density_df = textures_df = clefs_info = intervals_info = common_columns_df

        textures_df = pd.concat(
            [textures_df, all_dataframes[textures_list]], axis=1)
        density_df = pd.concat(
            [density_df, all_dataframes[density_list]], axis=1)
        clefs_info = pd.concat(
            [clefs_info, all_dataframes[clefs_info_list]], axis=1)
        clefs_info = clefs_info.dropna(how='all', axis=1)

        print(str(i) + " factor")

        for instrument in list(instruments):
            results_folder = os.path.join(main_results_path, instrument)
            if not os.path.exists(results_folder):
                os.mkdir(results_folder)

            # CAPTURING FEATURES that depend total or partially on each part
            emphasised_A_list = []
            # intervals_list = ['P-5', 'M3', 'M-2', 'm3', 'm-2', 'P1', 'P5', 'P4', 'P-4', 'm-3', 'M2', 'M-3', 'm2', 'm-6',
            #   'm6', 'M6', 'P8', 'P-8', 'd5', 'A1', 'M-6', 'M-7', 'A4', 'M-10', 'd-5', 'm7', 'm-7', 'P12', 'A-2', 'M9']
            '''
             'M3', 'M-2', 'P1', 'm3',
            'm-2', 'M-3', 'm2', 'M2', 'P4', 'P-4', 'A1', 'm-3', 'm6', 'm-6', 'A2',
            'M-7', 'm-9', 'P5', 'd-8', 'd5', 'P-8', 'M6', 'P8', 'd-4', 'm7', 'm-7',
            'P12', 'A-2', 'A4', 'P-5', 'M9', 'M-6', 'M7', 'M-10', 'd-5', 'A-4',
            'M10', 'm10', 'm13', 'd1'
            '''

            # Intervals_types_list = ['Part' + instrument + 'RepeatedNotes', 'Part' + instrument+' LeapsAscending', 'Part' + instrument+'LeapsDescending', 'Part' + instrument+'LeapsAll', 'Part' + instrument+'StepwiseMotionAscending', 'Part' + instrument+'StepwiseMotionDescending',  'Part' + instrument+'StepwiseMotionAll',  'Part' + instrument+'Total',  'Part' + instrument+'PerfectAscending',  'Part' + instrument+'PerfectDescending',  'Part' + instrument+'PerfectAll',
            # 'ScoreMajorAscending', 'ScoreMajorDescending', 'ScoreMajorAll', 'ScoreMinorAscending', 'ScoreMinorDescending', 'ScoreMinorAll', 'ScoreAugmentedAscending', 'ScoreAugmentedDescending', 'ScoreAugmentedAll', 'ScoreDiminishedAscending', 'ScoreDiminishedDescending', 'ScoreDiminishedAll', 'ScoreTotal1']
            '''
                'RepeatedNotes',
            'LeapsAscending', 'LeapsDescending', 'LeapsAll',
            'StepwiseMotionAscending', 'StepwiseMotionDescending',
            'StepwiseMotionAll', 'Total', 'PerfectAscending', 'PerfectDescending',
            'PerfectAll', 'MajorAscending', 'MajorDescending', 'MajorAll',
            'MinorAscending', 'MinorDescending', 'MinorAll', 'AugmentedAscending',
            'AugmentedDescending', 'AugmentedAll', 'DiminishedAscending',
            'DiminishedDescending', 'DiminishedAll', 'Total1']
            '''

            # intervals_info = pd.concat(
            #     [common_columns_df, all_dataframes[intervals_list]], axis=1)

            # Intervals_types = pd.concat(
            #     [common_columns_df, all_dataframes[Intervals_types_list]], axis=1)

            emphasised_scale_degrees_info_A = pd.concat(
                [common_columns_df, all_dataframes[emphasised_A_list]], axis=1)

            emphasised_scale_degrees_info_B = common_columns_df
            Intervals_types = pd.concat(
                [common_columns_df, all_dataframes[clefs_info_list]], axis=1)

            # dropping nans
            Intervals_types = Intervals_types.dropna(
                how='all', axis=1)
            emphasised_scale_degrees_info_A = emphasised_scale_degrees_info_A.dropna(
                how='all', axis=1)
            emphasised_scale_degrees_info_B = emphasised_scale_degrees_info_B.dropna(
                how='all', axis=1)
            intervals_info = intervals_info.dropna(how='all', axis=1)
            absolute_intervals = make_intervals_absolute(intervals_info)

            # 2. Get the additional_info dictionary (special case if there're no factors)
            additional_info = {"AriaLabel": ["AriaTitle"],
                               "AriaTitle": ["AriaLabel"]}  # solo agrupa aria
            if i == 0:
                rows_groups = {"AriaId": ([], "Alphabetic")}
                rg_keys = [rg[r][0] if rg[r][0] != [] else r for r in rg]
                for r in rg_keys:
                    if type(r) == list:
                        not_used_cols += r
                    else:
                        not_used_cols.append(r)
                # It a list, so it is applicable to all grouppings
                additional_info = ["AriaLabel", "AriaId", "Composer", "Year"]

            rg_groups = [[]]
            if i >= 2:  # 2 factors or more
                rg_groups = list(permutations(
                    list(forbiden_groups.keys()), i - 1))[4:]

                if i > 2:
                    prohibidas = ['Composer', 'Opera']
                    for g in rg_groups:
                        if "AriaId" in g:
                            g_rest = g[g.index("AriaId"):]
                            if any(p in g_rest for p in prohibidas):
                                rg_groups.remove(g)
                        elif "AriaLabel" in g:
                            g_rest = g[g.index("AriaLabel"):]
                            if any(p in g_rest for p in prohibidas):
                                rg_groups.remove(g)
                rg_groups = [r for r in rg_groups if r[0]
                             in list(metadata_columns)]  # ???

            results_path_factorx = path.join(main_results_path, instrument, str(
                i) + " factor") if i > 0 else path.join(main_results_path, instrument, "Data")
            if not os.path.exists(results_path_factorx):
                os.makedirs(results_path_factorx)

            # # MULTIPROCESSING (one process per group (year, decade, city, country...))
            # if sequential: # 0 and 1 factors
            for groups in rg_groups:
                # self._group_execution(groups, results_path_factorx, additional_info, i, self.sorting_lists, all_info, intervals_info, absolute_intervals,
                #                       Intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info)
                self._group_execution(
                    groups, results_path_factorx, additional_info, i, self.sorting_lists, density_df, textures_df)
                rows_groups = rg
                not_used_cols = nuc
            # else: # from 2 factors
            #     # process_executor = concurrent.futures.ProcessPoolExecutor()
            #     futures = [process_executor.submit(self._group_execution, groups, results_path_factorx, additional_info, i, sorting_lists, all_info, intervals_info, absolute_intervals, Intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info, sequential) for groups in rg_groups]
            #     kwargs = {'total': len(futures),'unit': 'it','unit_scale': True,'leave': True}
            #     for f in tqdm(concurrent.futures.as_completed(futures), **kwargs):
            #         rows_groups = rg
            #         not_used_cols = nuc

    #####################################################################
    # Function that generates the needed information for each grouping  #
    #####################################################################
    # def _group_execution(self, groups, results_path_factorx, additional_info, i, sorting_lists, all_info, intervals_info, absolute_intervals, Intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info):

    def _group_execution(self, groups, results_path_factorx, additional_info, i, sorting_lists, density_df, textures_df):

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
            os.makedirs(path.join(results_path, 'visualisations'))
        # MUTITHREADING
        try:
            # executor = concurrent.futures.ThreadPoolExecutor()
            # self.visualiser_lock = threading.Lock()
            # futures = []
            if not density_df.empty:
                densities(density_df, results_path, '-'.join(groups) + "_Densities.xlsx",
                          sorting_lists, self.visualiser_lock, groups if groups != [] else None, additional_info)
            if not textures_df.empty:
                textures(textures_df, results_path, '-'.join(groups) + "_Textures.xlsx",
                         sorting_lists, self.visualiser_lock, groups if groups != [] else None, additional_info)

            # if not all_info.empty:
            #     # futures.append(executor.submit(iValues, all_info, results_path, '-'.join(groups) + "_1Values.xlsx", sorting_lists,
            #     #                self.visualiser_lock, additional_info, True if i == 0 else False, groups if groups != [] else None))
            #     iValues(all_info, results_path, '-'.join(groups) + "_1Values.xlsx", sorting_lists,
            #             self.visualiser_lock, additional_info, True if i == 0 else False, groups if groups != [] else None)
                # if not intervals_info.empty:
                #     futures.append(executor.submit(iiaIntervals, intervals_info, '-'.join(groups) + "_2aIntervals.xlsx",
                #                    sorting_lists["Intervals"], results_path, sorting_lists, self.visualiser_lock, additional_info, groups if groups != [] else None))
                #     futures.append(executor.submit(iiaIntervals, absolute_intervals, '-'.join(groups) + "_2bIntervals_absolute.xlsx",
                #                    sorting_lists["Intervals_absolute"], results_path, sorting_lists, self.visualiser_lock, additional_info, groups if groups != [] else None))
                # if not Intervals_types.empty:
                #     futures.append(executor.submit(IIIIntervals_types, Intervals_types, results_path, '-'.join(groups) +
                #                    "_3Interval_typesIIIIntervals_types.xlsx", sorting_lists, self.visualiser_lock, groups if groups != [] else None, additional_info))
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
