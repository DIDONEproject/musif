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

if not os.path.exists(path.join(os.getcwd(), 'source', 'logs')):
    os.mkdir(path.join(os.getcwd(), 'source', 'logs'))


########################################################
# This function prints the names in the excell in bold
########################################################
def write_columns_titles(hoja, row, column, column_names):
    for c in column_names:
        hoja.cell(row, column).value = c
        hoja.cell(row, column).font = bold
        hoja.cell(row, column).fill = titles3Fill
        column += 1

################################################################################################################
# This function prints a row with the column names with variable size (each name can use more than one column) #
# Column_names will be a list of tuples (name, length)                                                         #
################################################################################################################


def write_columns_titles_variable_length(hoja, row, column, column_names, fill):
    for c in column_names:
        hoja.cell(row, column).value = c[0]
        hoja.cell(row, column).font = bold
        if c[0] != '':
            hoja.cell(row, column).fill = fill
        hoja.cell(row, column).alignment = center
        hoja.merge_cells(start_row=row, start_column=column,
                         end_row=row, end_column=column + c[1] - 1)
        column += c[1]


def print_averages_total(hoja, row, values, lable_column, values_column, average=False, per=False, exception=None):
    hoja.cell(row, lable_column).value = "Average" if average else "Total"
    hoja.cell(row, lable_column).fill = orangeFill

    for i, v in enumerate(values):
        if exception and i == exception:  # unicamente ocurre en % Trimmed en iValues
            hoja.cell(row, values_column).value = str(round(v * 100, 3)) + '%'
        else:
            hoja.cell(row, values_column).value = v if not per else str(v) + "%"
        values_column += 1


def print_averages_total_column(hoja, row, column, values, average=False, per=False):
    hoja.cell(row, column).value = "Average" if average else "Total"
    hoja.cell(row, column).fill = orangeFill
    row += 1
    for v in values:
        hoja.cell(row, column).value = v if not per else str(v) + "%"
        row += 1

###############################################################################################
# Function used to carry out every kind of computation needed, as determined by 'computation'
###############################################################################################


def compute_value(column_data, computation, ponderate_data, not_grouped_information, ponderate):
    value = 0
    if computation == "mean":
        if not ponderate:
            value = round(sum(column_data) / len(column_data), 3)
        else:
            s = 0
            for v, w in zip(column_data, ponderate_data):
                s += v * w
            value = round(s / sum(ponderate_data), 3)

    elif computation == "min":
        value = min(column_data)
    elif computation == "max":
        value = max(column_data)
    elif computation == "minNote":
        pitch_ps = [pitch.Pitch(n).ps for n in column_data]
        min_ps = min(pitch_ps)
        value = column_data.tolist()[pitch_ps.index(min_ps)]
    elif computation == "maxNote":
        pitch_ps = [pitch.Pitch(n).ps for n in column_data]
        max_ps = max(pitch_ps)
        value = column_data.tolist()[pitch_ps.index(max_ps)]
    elif computation == "meanNote":
        pitch_ps = [pitch.Pitch(n).ps for n in column_data]
        value = note_mean(pitch_ps)
    elif computation == "minInterval":
        interval_semitones = [interval.Interval(
            n).semitones for n in column_data]
        min_sem = min(interval_semitones)
        value = column_data.tolist()[interval_semitones.index(min_sem)]
    elif computation == "maxInterval":
        interval_semitones = [interval.Interval(
            n).semitones for n in column_data]
        max_sem = max(interval_semitones)
        value = column_data.tolist()[interval_semitones.index(max_sem)]
    elif computation == "meanInterval" or computation == "meanSemitones":
        lowest_notes_names = [a.split(',')[0] for a in column_data]
        max_notes_names = [a.split(',')[1] for a in column_data]
        min_notes_pitch = [pitch.Pitch(a).ps for a in lowest_notes_names]
        max_notes_pitch = [pitch.Pitch(a).ps for a in max_notes_names]
        mean_min = note_mean(min_notes_pitch, round_mean=True)
        mean_max = note_mean(max_notes_pitch, round_mean=True)
        i = interval.Interval(noteStart=note.Note(
            mean_min), noteEnd=note.Note(mean_max))
        if computation == "meanInterval":
            value = i.name
        else:
            value = i.semitones
    elif computation == "absoluteInterval" or computation == "absolute":
        lowest_notes_names = [a.split(',')[0] for a in column_data]
        max_notes_names = [a.split(',')[1] for a in column_data]
        min_notes_pitch = [pitch.Pitch(a).ps for a in lowest_notes_names]
        max_notes_pitch = [pitch.Pitch(a).ps for a in max_notes_names]
        minimisimo = min(min_notes_pitch)
        maximisimo = max(max_notes_pitch)
        noteStart = note.Note(
            lowest_notes_names[min_notes_pitch.index(minimisimo)])
        noteEnd = note.Note(max_notes_names[max_notes_pitch.index(maximisimo)])
        i = interval.Interval(noteStart=noteStart, noteEnd=noteEnd)
        if computation == "absoluteInterval":
            value = i.name
        else:
            value = i.semitones
    elif computation == "sum":
        value = np.nansum(column_data)
        # PONDERATE WITHT THE TOTAL ANALYSED IN THAT ROW
        if ponderate and value != 0 and column_data.name != "Total analysed":
            values = []
            # not_grouped_information needed for adding all the elements in total
            for i in range(len(column_data.tolist())):
                all_columns = not_grouped_information.columns.tolist()
                total_intervals = np.nansum([not_grouped_information.iloc[i, c] for c in range(
                    len(all_columns)) if 'All' not in all_columns[c]])
                intervals = column_data.tolist()[i]
                values.append(
                    (intervals * ponderate_data[i]) / total_intervals)

            value = np.nansum(values) / sum(ponderate_data)
            value = round(value * 100, 3)
    return value


def note_mean(pitch_ps, round_mean=False):
    mean_pitch = sum(pitch_ps) / len(pitch_ps)
    mean_pitch = mean_pitch if not round_mean else round(mean_pitch)
    if type(mean_pitch) == int or mean_pitch.is_integer():
        p = pitch.Pitch()
        p.ps = mean_pitch
        value = p.nameWithOctave.replace('-', 'b')
    else:
        pitch_up = pitch.Pitch()
        pitch_down = pitch.Pitch()
        pitch_up.ps = math.ceil(mean_pitch)
        pitch_down.ps = math.floor(mean_pitch)
        value = "-".join([pitch_up.nameWithOctave.replace('-', 'b'),
                          pitch_down.nameWithOctave.replace('-', 'b')])
    return value


def interval_mean(interval_semitones):
    mean_semitones = sum(interval_semitones) / len(interval_semitones)
    if mean_semitones.is_integer():
        i = interval.convertSemitoneToSpecifierGeneric(mean_semitones)
        value = str(i[0]) + str(i[1])
    else:
        i_up = math.ceil(mean_semitones)
        i_down = math.floor(mean_semitones)
        nup = interval.convertSemitoneToSpecifierGeneric(i_up)
        ndown = interval.convertSemitoneToSpecifierGeneric(i_down)
        value = "-".join([str(nup[0]) + str(nup[1]),
                          str(ndown[0]) + str(ndown[1])])
    return value

#####################################################################################
# Function to compute the average in every kind of variable, based on a computation #
#####################################################################################


def compute_average(dic_data, computation):
    value = 0
    if computation in ["mean", "min", "sum", "max", "absolute", "meanSemitones"]:
        value = round(sum(dic_data) / len(dic_data), 3)
    elif computation in ["minNote", "maxNote"]:
        pitch_ps = [pitch.Pitch(n).ps for n in dic_data]
        value = note_mean(pitch_ps)
    elif computation in ["meanNote"]:
        mean_dic_data = []
        for data in dic_data:
            pitches = [pitch.Pitch(n).ps for n in data.split('-')]
            mean_dic_data.append(sum(pitches) / len(pitches))
        value = note_mean(mean_dic_data)
    elif computation in ["minInterval", "maxInterval", "absoluteInterval"]:
        interval_semitones = [interval.Interval(n).semitones for n in dic_data]
        value = interval_mean(interval_semitones)
    elif computation == "meanInterval":
        mean_dic_data = []
        for data in dic_data:
            semitones = [interval.Interval(
                n).semitones for n in data.split('-')]
            mean_dic_data.append(sum(semitones) / len(semitones))
        value = interval_mean(mean_dic_data)

    return value

###########################################################################################################################################################
# This function is in charge of printing each group: 'Per Opera', 'Per City'...
#
#   hoja: the openpyxl object in which we will write
#   grouped: dataframe already grouped by the main factor and the additional information that it may show
#   row_number, column_number: row and column in which we will start to write the information
#   columns: list of the dataframe (grouped) column names that we need to access (as it doesn't necessarily correspond to the names that we want to print)
#   third_columns: list of the names of the columns that we need to print
#   computations_columns: information about the matematical computation that has to be done to each column (sum, mean...)
#   ----------------
#   first_columns: list of column names to print in first place, along with the number of columns that each has to embrace
#   second_columns: list of column names to print in second place, along with the number of columns that each has to embrace
#   per: boolean value to indicate if we need to compute the excel in absolute values or percentage (by default it is absolute)
#   average: boolean value to indicate if we want the average row at the last group's row
#   last_column: boolean value to indicate if we want a summarize on the last column
#   last_column_average: boolean to indicate if we want the last column to have each row's average (otherwise, the total is writen)
#   additional_info: number of extra columns containing additional info
#   ponderate: boolean to indicate if we want to ponderate the data printed or not
#   not_grouped_df: tuple containing the additional information columns and the dataframe without applying groupBy
#
###########################################################################################################################################################


def print_groups(hoja, grouped, row_number, column_number, columns, third_columns, computations_columns,
                 first_columns=None, second_columns=None, per=False, average=False, last_column=False,
                 last_column_average=False, additional_info=None, ponderate=False, not_grouped_df=None):
    len_add_info = 0  # Space for the possible column of additional information
    if additional_info:
        len_add_info = additional_info
    # WRITE THE COLUMN NAMES (<first>, <second> and third)
    if first_columns:
        write_columns_titles_variable_length(
            hoja, row_number, column_number + 1 + len_add_info, first_columns, titles1Fill)
        row_number += 1
    if second_columns:
        write_columns_titles_variable_length(
            hoja, row_number, column_number + 1 + len_add_info, second_columns, titles2Fill)
        row_number += 1
    starting_row = row_number
    write_columns_titles(hoja, row_number, column_number +
                         1 + len_add_info, third_columns)
    row_number += 1
    exception = -1
    total_analysed_column = "Total analysed" in columns
    cnumber = column_number
    # PRINT EACH ROW
    # store each result in case of need of calculating the percentage (per = True)
    valores_columnas = {c: [] for c in columns}
    # Subgroup: ex: Berlin when groupping by City
    for s, subgroup in enumerate(grouped):

        cnumber = column_number  # if not total_analysed_column else column_number + 1
        # Print row name
        if type(subgroup[0]) != tuple:  # It has no additional information
            # could be a tuple if we have grouped by more than one element
            hoja.cell(row_number, column_number).value = subgroup[0]
        else:
            for g in subgroup[0]:
                hoja.cell(row_number, cnumber).value = g
                cnumber += 1

        subgroup_data = subgroup[1]
        cnumber = column_number + 1 + len_add_info
        #
        total_analysed_row = [1]
        if not_grouped_df is not None:
            if type(subgroup[0]) != tuple:
                cond = not_grouped_df[1][not_grouped_df[0][0]] == subgroup[0]
                not_grouped_information = not_grouped_df[1][cond].drop(
                    not_grouped_df[0] + ['Total analysed'], axis=1)
            else:
                for sb in range(len(subgroup[0])):
                    cond = not_grouped_df[1][not_grouped_df[0]
                                             [sb]] == subgroup[0][sb]
                    not_grouped_information = not_grouped_df[1][cond]
                not_grouped_information = not_grouped_information.drop(
                    not_grouped_df[0] + ['Total analysed'], axis=1)
        else:
            not_grouped_information = None

        # COMPUTE EACH COLUMN'S VALUE FOR THE PRESENT ROW (SUBGROUP) AND PRINT IT
        for i, c in enumerate(columns):
            column_computation = computations_columns[i]
            value = compute_value(subgroup_data[c], column_computation, total_analysed_row,
                                  not_grouped_information, ponderate)  # absolute value
            if c == "Total analysed":
                total_analysed_row = subgroup_data[c].tolist()
                hoja.cell(row_number, cnumber).value = value

            if c == "% Trimmed":  # EXCEPTION
                hoja.cell(row_number, cnumber).value = str(
                    round(value * 100, 1)) + '%'
                cnumber += 1
                exception = i - 1
            elif not per:
                hoja.cell(row_number, cnumber).value = str(
                    value) + '%' if ponderate and column_computation == "sum" and c != "Total analysed" else str(value).replace(',', '.')
                cnumber += 1

            # store each value in case of needing to print the percentage
            valores_columnas[c].append(value)
        row_number += 1

    if total_analysed_column:  # We don't need Total analysed up to this point
        del valores_columnas['Total analysed']
        computations_columns = computations_columns[1:]

    last_used_row = row_number
    if per or last_column:  # This are the two conditions in which we need to transpose valores_columnas
        # Transpose valores_columnas to valores_filas (change perspective from column to rows)
        listas_columnas = list(valores_columnas.values())
        keys_columnas = list(valores_columnas.keys())
        valores_filas = []
        len_lists = len(listas_columnas[0])
        for i in range(len_lists):
            valores_filas.append(round(sum([lc[i] for x, lc in enumerate(
                listas_columnas) if "All" not in keys_columnas[x]]), 3))

    # PRINT EACH CELL IF PER IS TRUE, now that we have all the information
    if per:
        cn = column_number + len_add_info + \
            2 if total_analysed_column else column_number + len_add_info + 1
        for i in range(len(listas_columnas)):  # Traverse each column's information
            row_number = starting_row
            sum_column = sum(listas_columnas[i]) if sum(
                listas_columnas[i]) != 0 else 1
            for j in range(len(listas_columnas[i])):
                row_number += 1
                # COMPUTE THE HORIZONTAL OR VERTICAL AVERAGE (average within the present column or row)
                if average:
                    value = round(
                        (listas_columnas[i][j]/valores_filas[j])*100, 3)
                else:
                    value = round((listas_columnas[i][j]/sum_column)*100, 3)
                valores_columnas[keys_columnas[i]][j] = value if str(
                    value) != "nan" else 0  # update the value
                hoja.cell(row_number, cn).value = str(
                    value) + "%"  # print the value
            cn += 1

        cnumber = cn

    # RECALCULATE VALORES_FILAS AGAIN TO GET THE MOST UPDATED DATA
    listas_columnas = list(valores_columnas.values()
                           )  # Get the updated version
    if per:  # Compute valores_filas again
        valores_filas = []
        for i in range(len_lists):
            valores_filas.append(round(sum([lc[i] for x, lc in enumerate(
                listas_columnas) if "All" not in keys_columnas[x]]), 3))

    # PRINT THE LAST COLUMN (AVERAGE OR TOTAL)
    if last_column:
        if last_column_average:  # TODO: para qué?
            valores_filas = [round(vf / (len(listas_columnas) - len(
                [c for c in keys_columnas if "All" in c])), 3) for vf in valores_filas]
        # PRINT THE LAST COLUMN, CONTAINING THE TOTAL OR THE AVERAGE OF THE DATA
        print_averages_total_column(hoja, starting_row, cnumber, valores_filas, average=last_column_average,
                                    per=per or ponderate and all(c == "sum" for c in computations_columns))

    # PRINT LAST ROW (TOTAL OR AVERAGE)
    for i, c in enumerate(valores_columnas):
        if average:
            valores_columnas[c] = compute_average(
                valores_columnas[c], computations_columns[i])
        else:  # total
            valores_columnas[c] = round(sum(valores_columnas[c]), 3)

    final_values = list(valores_columnas.values())
    # Take the last value computed for the last column (average or total)
    if last_column:
        if average:
            final_values.append(
                round(sum(valores_filas) / len(valores_filas), 3))
        else:
            final_values.append(round(sum(valores_filas), 3))
    data_column = column_number + len_add_info + \
        2 if total_analysed_column else column_number + len_add_info + 1
    print_averages_total(hoja, last_used_row, final_values, column_number, data_column, average=average,
                         per=per or ponderate and all(c == "sum" for c in computations_columns), exception=exception)
    ###

    return last_used_row + 1, cnumber + 1


def get_groups_add_info(data, row, additional_info):
    if type(additional_info) == list:
        additional_info = [ai for ai in additional_info if ai in list(
            data.columns) and ai != row]
        groups = [row] + additional_info
        add_info = len(additional_info)
    else:  # es un diccionario que indica con la key con quien se tiene que agrupar
        if row in additional_info:
            groups = [row] + additional_info[row]
            add_info = len(additional_info[row])
        else:
            groups = [row]
            add_info = max(len(additional_info[k]) for k in additional_info)
    return groups, add_info


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
