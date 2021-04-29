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
import musif.extract.features.interval as interval
import musif.extract.features.lyrics as lyrics
from musif.common.constants import VOICE_FAMILY

class FeaturesGenerator:

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

    def _factor_execution(self, all_dataframes, factor):
        global rows_groups
        global not_used_cols

        main_results_path = os.path.join(self.main_results_path, 'results')
        rg = copy.deepcopy(rows_groups)
        nuc = copy.deepcopy(not_used_cols)

        # 1. Split all the dataframes to work individually
        common_columns_df = all_dataframes[metadata_columns]
        # self._cfg.scores_metadata['aria.csv'][0].keys()
        common_columns_df['Total analysed'] = 1.0

        clefs_info_list = ['Clef1', 'Clef2', 'Clef3']
        textures_list = []
        density_set = set([])
        notes_set=set([])
        intervals_list = []
        Intervals_types_list = []
        instruments = set([])
        if self.parts_list:
            instruments = self.parts_list
        else:
            for aria in all_dataframes['Scoring']:
                for a in aria.split(','):
                    instruments.add(a)

        instruments = [instrument[0].upper()+instrument[1:]
                       for instrument in instruments]

        # Getting general data that requires all info but is ran once

        for instrument in instruments:
            if instrument.lower().startswith('vn'):  # Violins are the exception in which we don't take Sound level data
                catch = 'Part'
                notes_set.add(catch + instrument + '_Notes')
            elif instrument.lower() in all_dataframes.Voices[0]:
                catch='Family'
                instrument=VOICE_FAMILY.capitalize()
                notes_set.add(catch + instrument + '_NotesMean')
            else:
                catch = 'Sound'
                if instrument.endswith('II'):
                    continue
                instrument = instrument.replace('I', '')
                notes_set.add(catch + instrument.replace('I', '') + '_NotesMean')

            density_set.add(
                catch + instrument + '_SoundingDensity')
            density_set.add(
                catch + instrument + '_SoundingMeasures')

        # Inizalizing new dataframes and defining those that don't depends on each part
        density_df = textures_df = clefs_info = intervals_info = all_info = common_columns_df

        textures_df = pd.concat(
            [textures_df, all_dataframes[[i for i in all_dataframes.columns if i.endswith('Texture')]], all_dataframes[list(notes_set)]], axis=1)
        density_df = pd.concat(
            [density_df, all_dataframes[list(density_set)],  all_dataframes[list(notes_set)]], axis=1)

        clefs_info = pd.concat(
            [clefs_info, all_dataframes[clefs_info_list]], axis=1)
        clefs_info = clefs_info.dropna(how='all', axis=1)

        flag=True #Variable to run common calculations only once
        
        print(str(factor) + " factor")

        emphasised_A_list = []

        # Running some processes that differ in each part
        for instrument in list(instruments):
            results_folder = os.path.join(main_results_path, instrument)

            if not os.path.exists(results_folder):
                os.makedirs(results_folder)

            # CAPTURING FEATURES that depend total or partially on each part
            catch='Part'+instrument +'_'
            all_info_list = [catch+interval.INTERVALLIC_MEAN, catch+interval.INTERVALLIC_STD, catch+interval.ABSOLUTE_INTERVALLIC_MEAN, catch+interval.ABSOLUTE_INTERVALLIC_STD, catch+interval.TRIMMED_ABSOLUTE_INTERVALLIC_MEAN,catch+interval.TRIMMED_ABSOLUTE_INTERVALLIC_STD,catch+interval.TRIMMED_INTERVALLIC_STD,catch+interval.TRIMMED_INTERVALLIC_MEAN,
                             catch+interval.ABSOLUTE_INTERVALLIC_TRIM_DIFF, catch+interval.ABSOLUTE_INTERVALLIC_TRIM_RATIO, catch+interval.ASCENDING_SEMITONES, catch+interval.ASCENDING_INTERVAL, catch+interval.DESCENDING_SEMITONES, catch+interval.DESCENDING_INTERVAL, catch + ambitus.HIGHEST_INDEX, catch + ambitus.LOWEST_NOTE, catch + ambitus.LOWEST_MEAN_NOTE, catch + ambitus.HIGHEST_MEAN_NOTE, catch + ambitus.HIGHEST_NOTE, catch + ambitus.LOWEST_MEAN_INDEX, catch + ambitus.LOWEST_INDEX, catch + ambitus.LOWEST_MEAN_NOTE, catch + ambitus.HIGHEST_MEAN_NOTE, catch + ambitus.HIGHEST_MEAN_INDEX, catch + ambitus.LARGEST_INTERVAL, catch + ambitus.LARGEST_SEMITONES, catch + ambitus.SMALLEST_INTERVAL, catch + ambitus.SMALLEST_SEMITONES, catch + ambitus.ABSOLUTE_INTERVAL, catch + ambitus.ABSOLUTE_SEMITONES, catch + ambitus.MEAN_INTERVAL, catch + ambitus.MEAN_SEMITONES]

            if 'Part'+instrument+lyrics.SYLLABIC_RATIO in all_dataframes.columns:
                all_info_list.append('Part'+instrument+lyrics.SYLLABIC_RATIO)

            for col in all_dataframes.columns:
                if col.startswith('PartInterval') or col.startswith('SoundInterval'):
                    intervals_list.append(col)
                    Intervals_types_list.append(col)
                # or all_dataframes[[i for i in all_dataframes.columns if i.endswith('Interval')]]]
                # Intervals_types_list = ['Part' + instrument + 'RepeatedNotes', 'Part' + instrument+' LeapsAscending', 'Part' + instrument+'LeapsDescending', 'Part' + instrument+'LeapsAll', 'Part' + instrument+'StepwiseMotionAscending', 'Part' + instrument+'StepwiseMotionDescending',  'Part' + instrument+'StepwiseMotionAll',  'Part' + instrument+'Total',  'Part' + instrument+'PerfectAscending',  'Part' + instrument+'PerfectDescending',  'Part' + instrument+'PerfectAll',
                    # 'ScoreMajorAscending', 'ScoreMajorDescending', 'ScoreMajorAll', 'ScoreMinorAscending', 'ScoreMinorDescending', 'ScoreMinorAll', 'ScoreAugmentedAscending', 'ScoreAugmentedDescending', 'ScoreAugmentedAll', 'ScoreDiminishedAscending', 'ScoreDiminishedDescending', 'ScoreDiminishedAll', 'ScoreTotal1']

            # Joining common info and part info
            all_info = pd.concat(
                [common_columns_df, all_dataframes[all_info_list]], axis=1)
            all_info.columns = [c.replace('Part'+instrument+'_', '')
                                for c in all_info.columns]
            intervals_info = pd.concat(
                [common_columns_df, all_dataframes[intervals_list]], axis=1)

            Intervals_types = pd.concat(
                [common_columns_df, all_dataframes[Intervals_types_list]], axis=1)

            emphasised_scale_degrees_info_A = pd.concat(
                [common_columns_df, all_dataframes[emphasised_A_list]], axis=1)

            emphasised_scale_degrees_info_B = common_columns_df

            # Dropping nans
            all_info = all_info.dropna(how='all', axis=1)
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
            if factor == 0:
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
            if factor >= 2:  # 2 factors or more
                rg_groups = list(permutations(
                    list(forbiden_groups.keys()), factor - 1))[4:]

                if factor > 2:
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
                factor) + " factor") if factor > 0 else path.join(main_results_path, instrument, "Data")
            if not os.path.exists(results_path_factorx):
                os.makedirs(results_path_factorx)

            common_data_path = path.join(main_results_path, 'Common', str(
                factor) + " factor") if factor > 0 else path.join(main_results_path, 'Common', "Data")

            if not os.path.exists(common_data_path):
                os.makedirs(common_data_path)
            if flag:
                for groups in rg_groups:
                    self._group_execution(
                        groups, common_data_path, additional_info, factor, self.sorting_lists, density_df=density_df, textures_df=textures_df)  # clefs_info)
                flag=False

            # # MULTIPROCESSING (one process per group (year, decade, city, country...))
            # if sequential: # 0 and 1 factors
            for groups in rg_groups:
                # self._group_execution(groups, results_path_factorx, additional_info, i, self.sorting_lists, all_info, intervals_info, absolute_intervals,
                #                       Intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info)
                self._group_execution(
                    groups, results_path_factorx, additional_info, factor, self.sorting_lists, all_info=all_info)
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

    def _group_execution(self, groups, results_path_factorx, additional_info, factor, sorting_lists, all_info=pd.DataFrame(), density_df=pd.DataFrame(), textures_df=pd.DataFrame(), clefs_info=pd.DataFrame()):

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
            if not all_info.empty:
                #     # futures.append(executor.submit(iValues, all_info, results_path, '-'.join(groups) + "_1Values.xlsx", sorting_lists,
                #     #                self.visualiser_lock, additional_info, True if i == 0 else False, groups if groups != [] else None))
                iValues(all_info, results_path, '-'.join(groups) + "_1Values.xlsx", sorting_lists,
                        self.visualiser_lock, additional_info, True if factor == 0 else False, groups if groups != [] else None)
            if not density_df.empty:
                densities(density_df, results_path, '-'.join(groups) + "_Densities.xlsx",
                          sorting_lists, self.visualiser_lock, groups if groups != [] else None, additional_info)
            if not textures_df.empty:
                textures(textures_df, results_path, '-'.join(groups) + "_Textures.xlsx",
                         sorting_lists, self.visualiser_lock, groups if groups != [] else None, additional_info)
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
            if not clefs_info.empty:
                # futures.append(executor.submit(iiaIntervals, clefs_info, '-'.join(groups) + "_5Clefs.xlsx",
                #                sorting_lists["Clefs"], results_path, sorting_lists, self.visualiser_lock, additional_info, groups if groups != [] else None))
                iiaIntervals(clefs_info, '-'.join(groups) + "_5Clefs.xlsx",
                             sorting_lists["Clefs"], results_path, sorting_lists, self.visualiser_lock, additional_info, groups if groups != [] else None)
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
        # except Exception as e:
        #     pass
