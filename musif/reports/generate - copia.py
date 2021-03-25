########################################################################
# WRITE MODULE
########################################################################
# This script is ment to read the intermediate files computed by the
# read module and perform several computations while grouping the data
# based on several characteristics.
# Writes the final report files as well as generates the visualisations
########################################################################
from os import path
import openpyxl
import os
from music21 import pitch, interval, note
import math
import numpy as np
import pandas as pd
import json
from itertools import combinations, permutations
import copy
import sys
import concurrent
from source.SortingGroupings import general_sorting, melody_sorting
from tqdm import tqdm
from source.visualisations import *
import shutil
import threading  # for the lock used for visualising, as matplotlib is not thread safe


olumn += 1


########################################
# data frame sorting for rows display  #
########################################
def sort_dataframe(data, column, sorting_lists, key_to_sort):
    if key_to_sort == "Alphabetic":
        dataSorted = data.sort_values(by=[column])
    else:
        form_list = sorting_lists[key_to_sort]  # es global
        indexes = []
        for i in data[column]:
            if str(i.lower().strip()) not in ["nan", 'nd']:
                value = i.strip() if key_to_sort not in [
                    'FormSorting', 'RoleSorting'] else i.strip().lower()
                try:
                    index = form_list.index(value)
                except:
                    index = 999
                    logger.warning('We do not have the value {} in the sorting list {}'.format(
                        value, key_to_sort))
                indexes.append(index)
            else:
                indexes.append(999)  # at the end of the list

        data.loc[:, "Ranks"] = indexes
        dataSorted = data.sort_values(by=["Ranks"])
        dataSorted.drop("Ranks", 1, inplace=True)
    return dataSorted


#####################################################################
# Function made for sorting the first list based on the second one  #
#####################################################################
def sort(list_to_sort, main_list):
    indexes = []
    huerfanos = []
    for i in list_to_sort:
        if i in main_list:
            indexes.append(main_list.index(i))
        else:
            huerfanos.append(i)
            logger.warning(
                'We do not have the appropiate sorting for {}'.format(i))
    indexes = sorted(indexes)
    list_sorted = [main_list[i] for i in indexes]
    return list_sorted + huerfanos

#######################################
# This function combines the 3 lists  #
#######################################


def get_lists_combined(first_element, second_list, third_list):
    final_list = []

    for s in third_list:
        if second_list != '':  # ocurre en las combinaciones de un elemento
            final_list.append(first_element + ',' + second_list + ',' + s)
        else:
            final_list.append(first_element + ',' + s)

    return final_list


########################################################################################
# This function returns the dictionary with the lists used to sort every group of data #
########################################################################################
def get_sorting_lists():
    RoleSorting = general_sorting.get_role_sorting()  # Only valid for DIDONE corpus
    FormSorting = general_sorting.get_form_sorting()
    KeySorting = general_sorting.get_key_sorting()
    KeySignatureSorting = general_sorting.get_KeySignature_sorting()
    KeySignatureGroupedSorted = general_sorting.get_KeySignatureType_sorting()
    TimeSignatureSorting = general_sorting.get_TimeSignature_sorting()
    TempoSorting = general_sorting.get_Tempo_sorting()
    TempoGroupedSorting1 = general_sorting.get_TempoGrouped1_sorting()
    TempoGroupedSorting2 = general_sorting.get_TempoGrouped2_sorting()
    clefs = general_sorting.get_Clefs_sorting()
    scoring_sorting = general_sorting.get_scoring_sorting()  # Long combination
    scoring_family = general_sorting.get_familiesCombinations_sorting()
    Intervals = melody_sorting.intervals_sorting()
    Intervals_absolute = melody_sorting.intervals_absolutte_sorting()
    scale_degrees = melody_sorting.MelodicDegrees_sorting()

    return {"RoleSorting": [i.lower() for i in RoleSorting],
            "FormSorting": [i.lower() for i in FormSorting],
            "KeySorting": KeySorting,
            "KeySignatureSorting": KeySignatureSorting,
            "KeySignatureGroupedSorted": KeySignatureGroupedSorted,
            "TimeSignatureSorting": TimeSignatureSorting,
            # a veces algunas puede ser nan, ya que no tienen tempo mark, las nan las ponemos al final
            "TempoSorting": TempoSorting + [''],
            "TempoGroupedSorting1": TempoGroupedSorting1 + [''],
            "TempoGroupedSorting2": TempoGroupedSorting2 + [''],
            "Intervals": Intervals,
            "Intervals_absolute": Intervals_absolute,
            "Clefs": clefs,
            "ScoringSorting": scoring_sorting,
            "ScoringFamilySorting": scoring_family,
            "ScaleDegrees": scale_degrees,
            }


###################################################################################################
# Function that generates all the files for each factor (choosed by the user or up to 1 by default)
#
# all_dataframes: list with all the needed dataframes
# main_results_path: path to the folder where the results will be stored
# i: number of factors
###################################################################################################
def factor_execution(all_dataframes, main_results_path, i, sorting_lists, sequential=True):
    global rows_groups
    global not_used_cols
    rg = copy.deepcopy(rows_groups)
    nuc = copy.deepcopy(not_used_cols)

    # 1. Split all the dataframes to work individually
    all_info, intervals_info, clefs_info, intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B = all_dataframes
    all_info = all_info.dropna(how='all', axis=1)
    intervals_info = intervals_info.dropna(how='all', axis=1)
    intervals_types = intervals_types.dropna(how='all', axis=1)
    emphasised_scale_degrees_info_A = emphasised_scale_degrees_info_A.dropna(
        how='all', axis=1)
    emphasised_scale_degrees_info_B = emphasised_scale_degrees_info_B.dropna(
        how='all', axis=1)
    clefs_info = clefs_info.dropna(how='all', axis=1)
    print(str(i) + " factor")

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
        rg_groups = list(permutations(list(forbiden_groups.keys()), i - 1))[4:]

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
        rg_groups = [r for r in rg_groups if r[0] in list(all_info.columns)]

    results_path_factorx = path.join(main_results_path, str(
        i) + " factor") if i > 0 else path.join(main_results_path, "Data")
    if not os.path.exists(results_path_factorx):
        os.mkdir(results_path_factorx)

    absolute_intervals = make_intervals_absolute(intervals_info)

    # MULTIPROCESSING (one process per group (year, decade, city, country...))
    if sequential:  # 0 and 1 factors
        for groups in rg_groups:
            group_execution(groups, results_path_factorx, additional_info, i, sorting_lists, all_info, intervals_info, absolute_intervals,
                            intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info, sequential)
            rows_groups = rg
            not_used_cols = nuc
    else:  # from 2 factors
        process_executor = concurrent.futures.ProcessPoolExecutor()
        futures = [process_executor.submit(group_execution, groups, results_path_factorx, additional_info, i, sorting_lists, all_info, intervals_info,
                                           absolute_intervals, intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info, sequential) for groups in rg_groups]
        kwargs = {'total': len(futures), 'unit': 'it',
                  'unit_scale': True, 'leave': True}
        for f in tqdm(concurrent.futures.as_completed(futures), **kwargs):
            rows_groups = rg
            not_used_cols = nuc

######################################################################################################
# Function used for printing the information in the corresponding excel files
#
# all_dataframes: list of the different intermediate dataframes obtained after the reading module
# results_path: path to the folder in which the excels will be generated
# num_factors: maximum number of factors to be generated
######################################################################################################


def write(all_dataframes, results_path, num_factors_max, sequential=False):
