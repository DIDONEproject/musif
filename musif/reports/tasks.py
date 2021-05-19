import copy
import logging
from multiprocessing import Lock
import os
from os import path
from typing import Dict, List
from matplotlib.pyplot import axis

import numpy as np
import openpyxl
from openpyxl.writer.excel import ExcelWriter
import pandas as pd
from pandas.core.frame import DataFrame
from musif.common.sort import sort

from .calculations import *
from .constants import *
from .visualisations import *
from .utils import *
import sys
from itertools import combinations, permutations
from musif.common.sort import sort_dataframe
import musif.extract.features.interval as interval
import musif.extract.features.ambitus as ambitus
import musif.extract.features.lyrics as lyrics
from musif.common.constants import VOICE_FAMILY

if not os.path.exists(path.join(os.getcwd(), 'logs')):
    os.mkdir(path.join(os.getcwd(), 'logs'))

fh = logging.FileHandler(
    path.join(os.getcwd(), 'logs', 'generation.log'), 'w+')
fh.setLevel(logging.ERROR)
logger = logging.getLogger("generation")
logger.addHandler(fh)

def _remove_folder_contents(path: str):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            _remove_folder_contents(file_path)

def _factor_execution(all_info: DataFrame, factor: int, parts_list: list, main_results_path: str, sorting_lists: dict):
        global rows_groups
        global not_used_cols

        main_results_path = os.path.join(main_results_path, 'results')
        rg = copy.deepcopy(rows_groups)
        nuc = copy.deepcopy(not_used_cols)

        # 1. Split all the dataframes to work individually
        common_columns_df = all_info[metadata_columns]

        common_columns_df['Total analysed'] = 1.0

        textures_list = []
        density_set = set([])
        notes_set=set([])
        intervals_list = []
        Intervals_types_list = []
        instruments = set([])
        emphasised_A_list = []

        if parts_list:
            instruments = parts_list
        else:
            for aria in all_info['Scoring']:
                for a in aria.split(','):
                    instruments.add(a)

        instruments = [instrument[0].upper()+instrument[1:]
                       for instrument in instruments]

        # Getting general data that requires all info but is ran once

        for instrument in instruments:
            if instrument.lower().startswith('vn'):  # Violins are the exception in which we don't take Sound level data
                catch = 'Part'
                notes_set.add(catch + instrument + '_Notes')
            elif instrument.lower() in all_info.Voices[0]:
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
        clefs_info=copy.deepcopy(common_columns_df)
        density_df=copy.deepcopy(common_columns_df)
        textures_df=copy.deepcopy(common_columns_df)

        common_columns_df.Clef2.replace('', np.nan, inplace=True)
        common_columns_df.Clef3.replace('', np.nan, inplace=True)
        intervals_info = Melody_values = common_columns_df

        textures = all_info[[i for i in all_info.columns if i.endswith('Texture')]]

        if not textures.empty: #We want textures to be processed in case there are any (not for cases where we request only 1 instrument type)
            textures_df = pd.concat(
                [textures_df, textures, all_info[list(notes_set)]], axis=1)
        else:
            textures_df=pd.DataFrame()

        density_df = pd.concat(
            [density_df, all_info[list(density_set)],  all_info[list(notes_set)]], axis=1)

        clefs_set= {i for i in all_info.Clef1 + all_info.Clef2 + all_info.Clef3}
        
        for clef in clefs_set:
            clefs_info[clef] = 0
            for r, j in enumerate(clefs_info.iterrows()):
                clefs_info[clef].iloc[r] = float(len([i for i in clefs_info[['Clef1','Clef2','Clef3']].iloc[r] if i == clef]))
        clefs_info.replace('', np.nan, inplace=True)
        clefs_info.dropna(how='all', axis=1, inplace=True)

        flag=True #Flag to run common calculations only once
        
        print(str(factor) + " factor")


        # Running some processes that differ in each part
        for instrument in list(instruments):
            results_folder = os.path.join(main_results_path, instrument)
            if not os.path.exists(results_folder):
                os.makedirs(results_folder)
                 
            # CAPTURING FEATURES that depend total or partially on each part
            catch = 'Part' + instrument + '_'
            # List of columns for melody parameters

            melody_values_list = [catch+interval.INTERVALLIC_MEAN, catch+interval.INTERVALLIC_STD, catch+interval.ABSOLUTE_INTERVALLIC_MEAN, catch+interval.ABSOLUTE_INTERVALLIC_STD, catch+interval.TRIMMED_ABSOLUTE_INTERVALLIC_MEAN,catch+interval.TRIMMED_ABSOLUTE_INTERVALLIC_STD,catch+interval.TRIMMED_INTERVALLIC_STD,catch+interval.TRIMMED_INTERVALLIC_MEAN,
                             catch+interval.ABSOLUTE_INTERVALLIC_TRIM_DIFF, catch+interval.ABSOLUTE_INTERVALLIC_TRIM_RATIO, catch+interval.ASCENDING_SEMITONES, catch+interval.ASCENDING_INTERVALS, catch+interval.DESCENDING_SEMITONES, catch+interval.DESCENDING_INTERVALS, catch + ambitus.HIGHEST_INDEX, catch + ambitus.LOWEST_NOTE, catch + ambitus.LOWEST_MEAN_NOTE, 
                             catch + ambitus.LOWEST_MEAN_INDEX, catch + ambitus.HIGHEST_MEAN_NOTE, catch + ambitus.HIGHEST_NOTE, catch + ambitus.LOWEST_INDEX, catch + ambitus.HIGHEST_MEAN_INDEX, catch + ambitus.LARGEST_INTERVAL, catch + ambitus.LARGEST_SEMITONES, catch + ambitus.SMALLEST_INTERVAL, catch + ambitus.SMALLEST_SEMITONES, catch + ambitus.MEAN_INTERVAL, catch + ambitus.MEAN_SEMITONES]

            if 'Part'+instrument+lyrics.SYLLABIC_RATIO in all_info.columns:
                melody_values_list.append('Part'+instrument+lyrics.SYLLABIC_RATIO)

            #Getting list of columns for intervals and scale degrees
            for col in all_info.columns:
                if col.startswith(catch+'Interval_'+'Count'):
                    intervals_list.append(col)
                elif col.startswith(catch+'Degree') and col.endswith('Count'):
                    emphasised_A_list.append(col)

            #Getting list of columns for intervals types
            # interval.INTERVALS_PERFECT_ASCENDING
            #TODO: add doble augmented
            
            intervals_types_list = [catch + interval.REPEATED_NOTES,catch + interval.LEAPS_ASCENDING, catch+ interval.LEAPS_DESCENDING, catch+interval.LEAPS_ALL, catch+ interval.STEPWISE_MOTION_ASCENDING, catch+ interval.STEPWISE_MOTION_DESCENDING, 
            catch+ interval.STEPWISE_MOTION_ALL]
            catch+='Intervals'
            intervals_types_list = intervals_types_list + [catch + interval.INTERVALS_PERFECT_ASCENDING,  catch+ interval.INTERVALS_PERFECT_DESCENDING,  catch+ interval.INTERVALS_PERFECT_ALL, catch +'MajorAscending', catch +'MajorDescending', catch +'MajorAll', catch +'MinorAscending', 
            catch +'MinorDescending', catch +'MinorAll', catch +'AugmentedAscending', catch +'AugmentedDescending', catch +'AugmentedAll', catch +'DiminishedAscending', catch +'DiminishedDescending', catch +'DiminishedAll',
            catch +'DoubleAugmentedAscending', catch +'DoubleAugmentedDescending', catch +'DoubleAugmentedAll',
            catch +'DoubleDiminishedAscending', catch +'DoubleDiminishedDescending', catch +'DoubleDiminishedAll']
            
            # Joining common info and part info, renaming columns for excel writing
            
            Melody_values = pd.concat(
                [common_columns_df, all_info[melody_values_list]], axis=1)
            Melody_values.columns = [c.replace('Part'+instrument+'_', '')
                                for c in Melody_values.columns]
            intervals_info = pd.concat(
                [common_columns_df, all_info[intervals_list]], axis=1)
            intervals_info.columns = [c.replace('Part'+instrument+'_'+'Interval_', '')
                                for c in intervals_info.columns]
            intervals_types = pd.concat([common_columns_df, all_info[intervals_types_list]], axis=1)
            intervals_types.columns = [c.replace('Part'+instrument+'_', '').replace('Intervals', '')
                                for c in intervals_types.columns]
            Emphasised_scale_degrees_info_A = pd.concat(
                [common_columns_df, all_info[emphasised_A_list]], axis=1)
            Emphasised_scale_degrees_info_A.columns = [c.replace('Part'+instrument+'_', '').replace('Degree', '').replace('Frequency', '')
                for c in Emphasised_scale_degrees_info_A.columns]

            Emphasised_scale_degrees_info_B = common_columns_df


            # Dropping nans
            Melody_values = Melody_values.dropna(how='all', axis=1)
            intervals_info.dropna(how='all', axis=1,inplace=True)
            intervals_types.dropna(
                how='all', axis=1,inplace=True)
            Emphasised_scale_degrees_info_A.dropna(
                how='all', axis=1,inplace=True)
            Emphasised_scale_degrees_info_B.dropna(
                how='all', axis=1,inplace=True)

            absolute_intervals = make_intervals_absolute(intervals_info)

            # Get the additional_info dictionary (special case if there're no factors)
            additional_info = {ARIA_LABEL: [TITLE],
                                TITLE: [ARIA_LABEL]}  # ONLY GROUP BY ARIA

            if factor == 0:
                rows_groups = {"AriaId": ([], "Alphabetic")}
                rg_keys = [rg[r][0] if rg[r][0] != [] else r for r in rg]
                for r in rg_keys:
                    if type(r) == list:
                        not_used_cols += r
                    else:
                        not_used_cols.append(r)
                # It a list, so it is applicable to all grouppings
                additional_info = [ARIA_LABEL, ARIA_ID, COMPOSER, YEAR]

            rg_groups = [[]]
            if factor >= 2:  # 2 factors or more
                rg_groups = list(permutations(
                    list(forbiden_groups.keys()), factor - 1))[4:]

                if factor > 2:
                    prohibidas = [COMPOSER, OPERA]
                    for g in rg_groups:
                        if ARIA_ID in g:
                            g_rest = g[g.index(ARIA_ID):]
                            if any(p in g_rest for p in prohibidas):
                                rg_groups.remove(g)
                        elif ARIA_LABEL in g:
                            g_rest = g[g.index(ARIA_LABEL):]
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
                    group_execution(
                        groups, common_data_path, additional_info, factor, sorting_lists, density_df=density_df, textures_df=textures_df, clefs_info=clefs_info)
                flag=False #FLAG guarantees this is processed only once (all common files)

            # # MULTIPROCESSING (one process per group (year, decade, city, country...))
            # if sequential: # 0 and 1 factors
            for groups in rg_groups:
                # group_execution(groups, results_path_factorx, additional_info, i, sorting_lists, Melody_values, intervals_info, absolute_intervals,
                #                       Intervals_types, Emphasised_scale_degrees_info_A, Emphasised_scale_degrees_info_B, clefs_info)
                group_execution(
                    groups, results_path_factorx, additional_info, factor, sorting_lists, Melody_values=Melody_values, intervals_info=intervals_info, intervals_types=intervals_types, Emphasised_scale_degrees_info_A = Emphasised_scale_degrees_info_A, Emphasised_scale_degrees_info_B = Emphasised_scale_degrees_info_B, absolute_intervals=absolute_intervals)
                rows_groups = rg
                not_used_cols = nuc
            # else: # from 2 factors
            #     # process_executor = concurrent.futures.ProcessPoolExecutor()
            #     futures = [process_executor.submit(group_execution, groups, results_path_factorx, additional_info, i, sorting_lists, Melody_values, intervals_info, absolute_intervals, Intervals_types, Emphasised_scale_degrees_info_A, Emphasised_scale_degrees_info_B, clefs_info, sequential) for groups in rg_groups]
            #     kwargs = {'total': len(futures),'unit': 'it','unit_scale': True,'leave': True}
            #     for f in tqdm(concurrent.futures.as_completed(futures), **kwargs):
            #         rows_groups = rg
            #         not_used_cols = nuc

#####################################################################
# Function that generates the needed information for each grouping  #
#####################################################################

def group_execution(groups: list, results_path_factorx: str, additional_info, factor: int, sorting_lists: Dict, Melody_values: DataFrame =pd.DataFrame(), density_df: DataFrame =pd.DataFrame(), textures_df: DataFrame =pd.DataFrame(),intervals_info: DataFrame =pd.DataFrame(),intervals_types: DataFrame =pd.DataFrame(), clefs_info: DataFrame =pd.DataFrame(), Emphasised_scale_degrees_info_A: DataFrame =pd.DataFrame(), Emphasised_scale_degrees_info_B: DataFrame =pd.DataFrame(), absolute_intervals: DataFrame =None):
    visualiser_lock = True #remve with threads

    if groups:
        # if sequential:
        results_path = path.join(results_path_factorx, '_'.join(groups))
        if not os.path.exists(results_path):
            os.mkdir(results_path)
    else:
        results_path = results_path_factorx
    if os.path.exists(path.join(results_path, 'visualisations')):
        _remove_folder_contents(
            path.join(results_path, 'visualisations'))
    else:
        os.makedirs(path.join(results_path, 'visualisations'))
    # MUTITHREADING
    try:
        # executor = concurrent.futures.ThreadPoolExecutor()
        # visualiser_lock = threading.Lock()
        # futures = []
        if not Melody_values.empty:
            #     # futures.append(executor.submit(Melody_values, Melody_values, results_path, '-'.join(groups) + "_1Values.xlsx", sorting_lists,
            #     #                visualiser_lock, additional_info, True if i == 0 else False, groups if groups != [] else None))
            Melody_values(Melody_values, results_path, '-'.join(groups) + "_MelodyValues.xlsx", sorting_lists,
                    visualiser_lock, additional_info, True if factor == 0 else False, groups if groups != [] else None )
        if not density_df.empty:
            Densities(density_df, results_path, '-'.join(groups) + "_Densities.xlsx",
                        sorting_lists, visualiser_lock, groups if groups != [] else None, additional_info)
        if not textures_df.empty:
            Textures(textures_df, results_path, '-'.join(groups) + "_Textures.xlsx",
                        sorting_lists, visualiser_lock, groups if groups != [] else None, additional_info)
        if not intervals_info.empty:
            Intervals(intervals_info, '-'.join(groups) + "_Intervals.xlsx",
                               sorting_lists["Intervals"], results_path, sorting_lists, visualiser_lock, additional_info, groups if groups != [] else None)
            Intervals(absolute_intervals, '-'.join(groups) + "_Intervals_absolute.xlsx",
                            sorting_lists["Intervals_absolute"], results_path, sorting_lists, visualiser_lock, additional_info, groups if groups != [] else None)
        if not intervals_types.empty:
            Intervals_types(intervals_types, results_path, '-'.join(groups) + "_Interval_types.xlsx", sorting_lists, visualiser_lock, groups if groups != [] else None, additional_info)
        if not Emphasised_scale_degrees_info_A.empty:
            Emphasised_scale_degrees(Emphasised_scale_degrees_info_A, sorting_lists["ScaleDegrees"], '-'.join(
                groups) + "_Scale_degrees.xlsx", results_path, sorting_lists, visualiser_lock, groups if groups != [] else None, additional_info)
        # if not Emphasised_scale_degrees_info_B.empty:
        #     Emphasised_scale_degrees( Emphasised_scale_degrees_info_B, sorting_lists["ScaleDegrees"], '-'.join(
        #         groups) + "_4bScale_degrees_relative.xlsx", results_path, sorting_lists, visualiser_lock, groups if groups != [] else None, additional_info)
        if not clefs_info.empty:
            Intervals(clefs_info, '-'.join(groups) + "_Clefs.xlsx",
                            sorting_lists["Clefs"], results_path, sorting_lists, visualiser_lock, additional_info, groups if groups != [] else None)
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

###########################################################################################################################################################
# Function is in charge of printing each group: 'Per Opera', 'Per City'...
#
#   sheet: the openpyxl object in which we will write
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

def print_groups(sheet: ExcelWriter, grouped:list, row_number: int, column_number: int, columns: list, third_columns: list, computations_columns: list,
                 first_columns: list = None, second_columns: List=None, per: bool=False, average:bool=False, last_column: bool=False,
                 last_column_average: bool=False, additional_info: DataFrame=None, ponderate: bool=False, not_grouped_df:DataFrame=None):
    len_add_info = 0  # Space for the possible column of additional information
    if additional_info:
        len_add_info = additional_info
    # WRITE THE COLUMN NAMES (<first>, <second> and third)
    if first_columns:
        write_columns_titles_variable_length(
            sheet, row_number, column_number + 1 + len_add_info, first_columns, titles1Fill)
        row_number += 1
    if second_columns:
        write_columns_titles_variable_length(
            sheet, row_number, column_number + 1 + len_add_info, second_columns, titles2Fill)
        row_number += 1
    starting_row = row_number
    write_columns_titles(sheet, row_number, column_number +
                         1 + len_add_info, third_columns)
    row_number += 1
    exception = -1
    total_analysed_column = "Total analysed" in columns
    cnumber = column_number
    # PRINT EACH ROW
    # store each result in case of need of calculating the percentage (per = True)
    valores_columnas = {c: [] for c in columns}

    # Subgroup: ex: Berlin when groupping by Territory
    for s, subgroup in enumerate(grouped):

        cnumber = column_number  
        # Print row name
        if type(subgroup[0]) != tuple:  # It has no additional information
            # could be a tuple if we have grouped by more than one element
            sheet.cell(row_number, column_number).value = subgroup[0]
        else:
            for g in subgroup[0]:
                sheet.cell(row_number, cnumber).value = g
                cnumber += 1

        subgroup_data = subgroup[1]
        cnumber = column_number + 1 + len_add_info

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

        # compute each column's value for the present row (subgroup) and print it
        for i, c in enumerate(columns):
            column_computation = computations_columns[i]
            extra_info = []
            if column_computation == 'mean_density':
                extra_info = subgroup_data[c+'Measures']
                value = compute_value(subgroup_data[c], column_computation, total_analysed_row,
                                      not_grouped_information, ponderate, extra_info=extra_info)
                                      
            elif column_computation == 'mean_texture':
                notes = subgroup_data[c.split('/')[0]+'Notes']
                notes_next = subgroup_data[c.split('/')[1]+'Notes']
                value = compute_value(notes, column_computation, total_analysed_row,
                                      not_grouped_information, ponderate, extra_info=notes_next) 
            else:

                value = compute_value(subgroup_data[c], column_computation, total_analysed_row,
                                      not_grouped_information, ponderate)  # absolute value
            if c == "Total analysed":
                total_analysed_row = subgroup_data[c].tolist()
                sheet.cell(row_number, cnumber).value = value

            if c == interval.ABSOLUTE_INTERVALLIC_TRIM_RATIO:  # EXCEPTION
                #TODO: wht is this ?????
                sheet.cell(row_number, cnumber).value = str(
                    round(value * 100, 1)) + '%'
                cnumber += 1
                exception = i - 1
            elif not per:
                sheet.cell(row_number, cnumber).value = str(
                    value) + '%' if ponderate and column_computation == "sum" and c != "Total analysed" else str(value).replace(',', '.')
                cnumber += 1

            # store each value in case of needing to print the percentage
            valores_columnas[c].append(value)
        row_number += 1

    if total_analysed_column:  # We don't need Total analysed from this point
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
                sheet.cell(row_number, cn).value = str(
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
        print_averages_total_column(sheet, starting_row, cnumber, valores_filas, average=last_column_average,
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
    print_averages_total(sheet, last_used_row, final_values, column_number, data_column, average=average,
                         per=per or ponderate and all(c == "sum" for c in computations_columns), exception=exception)
    ###

    return last_used_row + 1, cnumber + 1


##########################################################################################################
# Function in charge of printting the data, the arguments are the same as the explained in excel_sheet  #
##########################################################################################################


def row_iteration(sheet: ExcelWriter, columns: list, row_number: int, column_number: int, data: DataFrame, third_columns: list, computations_columns: List[str], sorting_lists: list, group: list=None, first_columns: list=None, second_columns: list=None, per: bool=False, average: bool=False, last_column: bool=False, last_column_average: bool=False,
                  columns2: list=None, data2: DataFrame=None, third_columns2: list=None, computations_columns2: list=None, first_columns2: list=None, second_columns2: list=None, additional_info: list=[], ponderate: bool =False):
    all_columns = list(data.columns)
    for row in rows_groups:  # Geography, Dramma, Opera, Aria, Label, Composer...
        if row in all_columns or any(sub in all_columns for sub in rows_groups[row][0]):
            forbiden = []
            if group != None:
                forbiden = [forbiden_groups[group[i]]
                            for i in range(len(group))]
                forbiden = [item for sublist in forbiden for item in sublist]
            if group == None or row not in forbiden:
                # 1. Write the Title in Yellow
                sheet.cell(row_number, column_number).value = "Per " + row
                sheet.cell(row_number, column_number).fill = yellowFill
                row_number += 1
                sorting = rows_groups[row][1]
                # 2. Write the information depending on the subgroups (ex: Geography -> City, Country)
                if len(rows_groups[row][0]) == 0:  # No subgroups
                    starting_row = row_number
                    # Sort the dataframe based on the json sorting_lists in Json_extra
                    data = sort_dataframe(data, row, sorting_lists, sorting)
                    groups_add_info, add_info = get_groups_add_info(
                        data, row, additional_info)
                    row_number, last_column_used = print_groups(sheet, data.groupby(groups_add_info, sort=False), row_number, column_number, columns, third_columns, computations_columns, first_columns, second_columns, per=per,
                                                                average=average, last_column=last_column, last_column_average=last_column_average, additional_info=add_info, ponderate=ponderate, not_grouped_df=(groups_add_info, data[groups_add_info + columns]))
                    if columns2 != None:  # Second subgroup
                        groups_add_info, add_info = get_groups_add_info(
                            data, row, additional_info)
                        if data2 is not None:
                            data2 = sort_dataframe(
                                data2, row, sorting_lists, sorting)
                        _, _ = print_groups(sheet, data.groupby(groups_add_info, sort=False) if data2 is None else data2.groupby(groups_add_info, sort=False), starting_row, last_column_used + 1, columns2, third_columns2, computations_columns2, first_columns2,
                                            second_columns2, per=per, average=average, last_column=last_column, last_column_average=last_column_average, additional_info=add_info, ponderate=ponderate, not_grouped_df=(groups_add_info, data[groups_add_info + columns]))
                else:  # has subgroups, ex: row = Date, subgroups: Year
                    if rows_groups[row][0] == [CHARACTER, ROLE, GENDER]:
                        data_joint = data.copy()
                        data = split_voices(data)
                    for i, subrows in enumerate(rows_groups[row][0]):
                        if (subrows == None or subrows not in forbiden) and subrows in all_columns:
                            if "Tempo" in subrows:
                                data[subrows] = data[subrows].fillna('')
                            starting_row = row_number
                            sort_method = sorting[i]
                            sheet.cell(
                                row_number, column_number).value = subrows
                            sheet.cell(
                                row_number, column_number).fill = greenFill
                            data = sort_dataframe(
                                data, subrows, sorting_lists, sort_method)

                            groups_add_info, add_info = get_groups_add_info(
                                data, subrows, additional_info)
                            row_number, last_column_used = print_groups(sheet, data.groupby(groups_add_info, sort=False), row_number, column_number, columns, third_columns, computations_columns, first_columns, second_columns, per=per,
                                                                        average=average, last_column=last_column, last_column_average=last_column_average, additional_info=add_info, ponderate=ponderate, not_grouped_df=(groups_add_info, data[groups_add_info + columns]))
                            if columns2 != None:  # Second subgroup
                                if "Tempo" in subrows and data2 is not None:
                                    data2[subrows] = data2[subrows].fillna('')
                                if data2 is not None:
                                    data2 = sort_dataframe(
                                        data2, subrows, sorting_lists, sort_method)
                                groups_add_info, add_info = get_groups_add_info(
                                    data, subrows, additional_info)
                                _, _ = print_groups(sheet, data.groupby(groups_add_info, sort=False) if data2 is None else data2.groupby(groups_add_info, sort=False), starting_row, last_column_used + 1, columns2, third_columns2, computations_columns2, first_columns2,
                                                    second_columns2, per=per, average=average, last_column=last_column, last_column_average=last_column_average, additional_info=add_info, ponderate=ponderate, not_grouped_df=(groups_add_info, data[groups_add_info + columns]))

                            row_number += 1
                    if rows_groups[row][0] == [CHARACTER, ROLE, GENDER]:
                        data = copy.deepcopy(data_joint)
                row_number += 1
    return row_number


def excel_sheet(sheet: ExcelWriter, columns: list, data: DataFrame, third_columns: list, computations_columns: list, sorting_lists: list, groups: list=None, first_columns: list=None, second_columns: list=None, per: bool=False, average: bool=False, last_column: bool=False, last_column_average: bool=False,
                 columns2: list=None, data2: DataFrame=None, third_columns2: list=None, computations_columns2: list=None, first_columns2: list=None, second_columns2: list=None, additional_info: list=[], ponderate: bool=False):

    row_number = 1  # we start writing in row 1
    column_number = 1
    if groups == None:
        row_iteration(sheet, columns, row_number, column_number, data, third_columns, computations_columns, sorting_lists, first_columns=first_columns, second_columns=second_columns, per=per,
                      average=average, last_column=last_column, last_column_average=last_column_average, columns2=columns2, data2=data2, third_columns2=third_columns2, computations_columns2=computations_columns2, first_columns2=first_columns2, second_columns2=second_columns2, additional_info=additional_info, ponderate=ponderate)
    else:
        # we may be grouping by more than 2 factors
        data_grouped = data.groupby(list(groups))

        last_printed = {i: ('', 0) for i in range(len(groups))}
        for group, group_data in data_grouped:
            cnumber = column_number
            group = [group] if type(group) != tuple else group
            for i, g in enumerate(group):
                if last_printed[i][0] != g:
                    sheet.cell(row_number, cnumber).value = g
                    sheet.cell(row_number, cnumber).fill = factors_Fill[i]
                    sheet.cell(row_number, cnumber).font = bold
                    counter_g = data[groups[i]].tolist().count(g)
                    sheet.cell(row_number, cnumber + 1).value = counter_g
                    if last_printed[i][0] != '':
                        sheet.merge_cells(
                            start_row=last_printed[i][1], start_column=i + 1, end_row=row_number - 2, end_column=i + 1)
                        sheet.cell(last_printed[i][1],
                                  i + 1).fill = factors_Fill[i]

                    last_printed[i] = (g, row_number + 1)

                row_number += 1
                cnumber += 1
            data2_grouped = None
            if data2 is not None:
                data2_grouped = data2.groupby(list(groups)).get_group(
                    group if len(group) > 1 else group[0])
            rn = row_iteration(sheet, columns, row_number, cnumber, group_data, third_columns, computations_columns, sorting_lists, group=groups, first_columns=first_columns, second_columns=second_columns, per=per,
                               average=average, last_column=last_column, last_column_average=last_column_average, columns2=columns2, data2=data2_grouped, third_columns2=third_columns2, computations_columns2=computations_columns2, first_columns2=first_columns2, second_columns2=second_columns2, additional_info=additional_info, ponderate=ponderate)
            row_number = rn
        # merge last cells
        for i, g in enumerate(group):
            if last_printed[i][0] == g:
                sheet.merge_cells(
                    start_row=last_printed[i][1], start_column=i + 1, end_row=row_number - 2, end_column=i + 1)
                sheet.cell(last_printed[i][1],  i + 1).fill = factors_Fill[i]

########################################################################
# Function ment to write the Melody_values excel
# -------
# data: Melody_values dataframe
# results_path: where to store the data
# name: name that the excel will take
# sorting lists: lists that will be used for sorting the results
# visualiser_lock: lock used to avoid deadlocks, as matplotlib is not thread safe
# additional info: columns additional to each
# remove_columns: used for factor 0, to avoid showing unusefull information
# groups: used for factor > 1
########################################################################

def Melody_values(data: DataFrame, results_path: str, name: str, sorting_lists: list, visualiser_lock: Lock, additional_info: list=[], remove_columns: bool=False, groups: list=None):
    # try:
        workbook = openpyxl.Workbook()
        data.rename(columns={interval.INTERVALLIC_MEAN: "Intervallic ratio", interval.TRIMMED_ABSOLUTE_INTERVALLIC_MEAN: "Trimmed intervallic ratio", interval.ABSOLUTE_INTERVALLIC_TRIM_DIFF: "dif. Trimmed",
                             interval.ABSOLUTE_INTERVALLIC_MEAN: "Absolute intervallic ratio", interval.INTERVALLIC_STD: "Std", interval.ABSOLUTE_INTERVALLIC_STD: "Absolute Std", interval.ABSOLUTE_INTERVALLIC_TRIM_RATIO: "% Trimmed"}, inplace=True)
        
        data.rename(columns={ambitus.LOWEST_INDEX: "LowestIndex", ambitus.HIGHEST_INDEX: "HighestIndex", ambitus.HIGHEST_MEAN_INDEX: "HighestMeanIndex", ambitus.LOWEST_MEAN_INDEX: "LowestMeanIndex",
             ambitus.LOWEST_NOTE: "LowestNote", ambitus.LOWEST_MEAN_NOTE: "LowestMeanNote",ambitus.HIGHEST_MEAN_NOTE: "HighestMeanNote", ambitus.LOWEST_MEAN_INDEX: "LowestMeanIndex",ambitus.HIGHEST_NOTE: "HighestNote" }, inplace=True)
        # HOJA 1: STATISTICAL_VALUES
        column_names = ["Total analysed", "Intervallic ratio", "Trimmed intervallic ratio", "dif. Trimmed",
                        "% Trimmed", "Absolute intervallic ratio", "Std", "Absolute Std"]

        if lyrics.SYLLABIC_RATIO in data.columns:
            data.rename(columns={lyrics.SYLLABIC_RATIO: 'Syllabic ratio'})
            column_names.append('Syllabic ratio')

        # HAREMOS LA MEDIA DE TODAS LAS COLUMNAS
        computations = ['sum'] + ["mean"]*(len(column_names) - 1)
        excel_sheet(workbook.create_sheet("Statistical_values"), column_names, data, column_names, computations,
                     sorting_lists, groups=groups, average=True, additional_info=additional_info, ponderate=True)

        # HOJA 2: AMBITUS
        first_column_names = [("", 1), ("Lowest", 2), ("Highest", 2), ("Lowest", 2), ("Highest", 2), (
            "Ambitus", 6)] if not remove_columns else [("", 1), ("Lowest", 2), ("Highest", 2), ("Ambitus", 2)]

        second_column_names = [("", 5), ("Mean", 2), ("Mean", 2), ("Largest", 2), ("Smallest", 2), ("Mean", 2)] if not remove_columns else [("", 5), ("Largest", 2)]

        third_columns_names = ["Total analysed", "Note", "Index", "Note", "Index", "Note", "Index", "Note", "Index", "Semitones", "Interval", "Semitones", "Interval",
         "Semitones", "Interval"] if not remove_columns else ["Total analysed", "Note", "Index", "Note", "Index", "Semitones", "Interval"]

        computations = ["sum", "minNote", "min", "maxNote", "max", 'meanNote', 'mean', 'meanNote', 'mean', 'max', "maxInterval", 'min', "minInterval", 'absolute',
                        'absoluteInterval', "meanSemitones", "meanInterval"] if not remove_columns else ["sum", "minNote", "min", "maxNote", "max", 'max', "maxInterval"]

        columns = columns_alike_our_data(
            third_columns_names, second_column_names, first_column_names)

        excel_sheet(workbook.create_sheet("Ambitus"), columns, data, third_columns_names, computations, sorting_lists, groups=groups,
                     first_columns=first_column_names, second_columns=second_column_names, average=True, additional_info=additional_info)

        # HOJA 3: LARGEST_LEAPS
        second_column_names = [("", 1), ("Ascending", 2), ("Descending", 2)]
        third_columns_names = ["Total analysed",
                               "Semitones", "Intervals", "Semitones", "Intervals"]
        columns = columns_alike_our_data(
            third_columns_names, second_column_names)
        computations = ["sum", "max", "maxInterval", "min", "minInterval"]

        excel_sheet(workbook.create_sheet("Largest_leaps"), columns, data, third_columns_names, computations,
                     sorting_lists, groups=groups, second_columns=second_column_names, average=True, additional_info=additional_info)

        if "Sheet" in workbook.get_sheet_names():  # Delete the default sheet
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        # with visualiser_lock:
        # VISUALISATIONS
        columns_visualisation = [
            'Intervallic ratio', 'Trimmed intervallic ratio', 'Std']
        if groups:
            data_grouped = data.groupby(list(groups))
            for g, datag in data_grouped:
                result_visualisations = path.join(
                    results_path, 'visualisations', g)
                if not os.path.exists(result_visualisations):
                    os.mkdir(result_visualisations)

                name_bar = path.join(
                    result_visualisations, name.replace('.xlsx', '.png'))
                ivalues_bar_plot(
                    name_bar, datag, columns_visualisation, second_title=str(g))
                name_box = path.join(
                    result_visualisations, 'Ambitus' + name.replace('.xlsx', '.png'))
                box_plot(name_box, datag, second_title=str(g))
        elif len(not_used_cols) == 5:  # 1 Factor. TODO: Try a different criteria
            groups = [i for i in rows_groups]
            exceptions_list = [ROLE, KEYSIGNATURE, TEMPO, YEAR, CITY, SCENE]
            for row in rows_groups:
                plot_name = name.replace(
                    '.xlsx', '') + 'Per ' + str(row.replace('Aria','').upper()) + '.png'
                name_bar =path.join(results_path,'visualisations', plot_name)
                if row not in not_used_cols:
                    if len(rows_groups[row][0]) == 0:  # no sub-groups
                        data_grouped = data.groupby(row, sort=True)
                        if data_grouped:
                            ivalues_bar_plot(name_bar, data, columns_visualisation, second_title='_Per_' + str(row.replace('Aria','').upper()))
                            name_box = path.join(results_path,'visualisations', 'Ambitus'+'Per ' + str(row.upper())+name.replace('.xlsx', '.png'))
                            box_plot(name_box, data, second_title='Per '+ str(row.replace('Aria','').upper()))
                    else: #subgroups
                            i=0
                            for i, subrow in enumerate(rows_groups[row][0]):
                                if subrow not in exceptions_list:
                                    plot_name = name.replace(
                                        '.xlsx', '') + '_Per_' + str(row.upper()) + '_' + str(subrow) + '.png'
                                    name_bar = results_path + '\\visualisations\\' + plot_name
                                    data_grouped = data.groupby(subrow)
                                    ivalues_bar_plot(name_bar, data, columns_visualisation)
                                    name_box = path.join(
                                    results_path, 'visualisations', 'Ambitus' + name.replace('.xlsx', '.png'))
                                    box_plot(name_box, data)
        else:                   
            name_bar = path.join(results_path,path.join('visualisations', name.replace('.xlsx', '.png')))
            ivalues_bar_plot(name_bar, data, columns_visualisation)
            name_box = path.join(
                results_path, 'visualisations', 'Ambitus' + name.replace('.xlsx', '.png'))
            box_plot(name_box, data)
    # except Exception as e:
    #     logger.error('{}   Problem found:'.format(name), exc_info=True)


def Intervals(data: DataFrame, name: str, sorting_list: list, results_path: str, sorting_lists: list, visualiser_lock: Lock, additional_info: list=[], groups: list=None):
    # try:
        workbook = openpyxl.Workbook()
        all_columns = data.columns.tolist()
        general_cols = copy.deepcopy(not_used_cols)
        for row in rows_groups:
            if len(rows_groups[row][0]) == 0:
                general_cols.append(row)
            else:
                general_cols += rows_groups[row][0]

        # nombres de todos los intervalos
        third_columns_names_origin = set(all_columns) - set(general_cols)
        third_columns_names_origin = sort(
            third_columns_names_origin, sorting_list)
        third_columns_names = ['Total analysed'] + third_columns_names_origin

        # esta sheet va de sumar, así que en todas las columnas el cómputo que hay que hacer es sumar!
        computations = ["sum"]*len(third_columns_names)

        excel_sheet(workbook.create_sheet("Weighted"), third_columns_names, data, third_columns_names, computations, sorting_lists,
                     groups=groups, average=True, last_column=True, last_column_average=False, additional_info=additional_info, ponderate=True)
        excel_sheet(workbook.create_sheet("Horizontal Per"), third_columns_names, data, third_columns_names, computations, sorting_lists,
                     groups=groups, per=True, average=True, last_column=True, last_column_average=False, additional_info=additional_info)
        excel_sheet(workbook.create_sheet("Vertical Per"), third_columns_names, data, third_columns_names, computations, sorting_lists,
                     groups=groups, per=True, average=False, last_column=True, last_column_average=True, additional_info=additional_info)

        if "Sheet" in workbook.get_sheet_names():  # Delete the default sheet
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        # with visualiser_lock:
        # VISUALISATIONS
        if 'Clefs' in name:
            title = 'Use of clefs'
        elif 'Intervals_absolute' in name:
            title = 'Presence of intervals (direction dismissed)'
        else:
            title = 'Presence of intervals (ascending and descending)'

        if groups:
            data_grouped = data.groupby(list(groups))
            for g, datag in data_grouped:
                result_visualisations = path.join(
                    results_path, 'visualisations', g)
                if not os.path.exists(result_visualisations):
                    os.mkdir(result_visualisations)

                name_bar = path.join(
                    result_visualisations, name.replace('.xlsx', '.png'))
                bar_plot(name_bar, datag, third_columns_names_origin,
                            'Intervals' if 'Clef' not in name else 'Clefs', title, second_title=str(g))
        else:
            name_bar = path.join(
                results_path, 'visualisations', name.replace('.xlsx', '.png'))
            bar_plot(name_bar, data, third_columns_names_origin,
                        'Intervals' if 'Clef' not in name else 'Clefs', title)
    # except Exception as e:
    #     logger.error('{}  Problem found:'.format(name), exc_info=True)

#########################################################
# Function to generate the file Intervals_types.xlsx  #
#########################################################

def Intervals_types(data: DataFrame, results_path: str, name: str, sorting_lists: list, visualiser_lock: Lock, groups=None, additional_info: list=[]):
    # try:
        workbook = openpyxl.Workbook()

        second_column_names = [("", 2), ("Leaps", 3), ("StepwiseMotion", 3)]
        second_column_names2 = [('', 1), ("Perfect", 3), ("Major", 3),
                                ("Minor", 3), ("Augmented", 3), ("Diminished", 3)]
        third_columns_names = ['Total analysed', "RepeatedNotes",
                               "Ascending", "Descending", "All", "Ascending", "Descending", "All"]
        third_columns_names2 = ['Total analysed', "Ascending", "Descending", "All", "Ascending", "Descending", "All",
                                "Ascending", "Descending", "All", "Ascending", "Descending", "All", "Ascending", "Descending", "All"]
        computations = ["sum"]*len(third_columns_names)
        computations2 = ['sum']*len(third_columns_names2)
        columns = columns_alike_our_data(
            third_columns_names, second_column_names)
        columns2 = columns_alike_our_data(
            third_columns_names2, second_column_names2)

        excel_sheet(workbook.create_sheet("Weighted"), columns, data, third_columns_names, computations, sorting_lists, groups=groups, last_column=True, last_column_average=False, second_columns=second_column_names, average=True,
                     columns2=columns2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, additional_info=additional_info, ponderate=True)
        excel_sheet(workbook.create_sheet("Horizontal Per"), columns, data, third_columns_names, computations, sorting_lists, groups=groups, second_columns=second_column_names, per=True, average=True, last_column=True, last_column_average=False,
                     columns2=columns2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, additional_info=additional_info)
        excel_sheet(workbook.create_sheet("Vertical Per"), columns, data, third_columns_names, computations, sorting_lists, groups=groups, second_columns=second_column_names, per=True, average=False, last_column=True, last_column_average=True,
                     columns2=columns2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, additional_info=additional_info)

        # borramos la sheet por defecto
        if "Sheet" in workbook.get_sheet_names():
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        # with visualiser_lock:
        # VISUALISATIONS
        if groups:
            data_grouped = data.groupby(list(groups))
            for g, datag in data_grouped:
                result_visualisations = path.join(
                    results_path, 'visualisations', g)
                if not os.path.exists(result_visualisations):
                    os.mkdir(result_visualisations)

                name1 = path.join(result_visualisations,
                                    name.replace('.xlsx',  '') + '_AD.png')
                pie_plot(name1, datag, second_title=str(g))
                name2 = path.join(result_visualisations,
                                    name.replace('.xlsx',  '.png'))
                double_bar_plot(name2, data, second_title=str(g))
        else:
            name1 = path.join(results_path, 'visualisations',
                                name.replace('.xlsx', '') + '_AD.png')
            pie_plot(name1, data)
            name2 = path.join(results_path, 'visualisations',
                                name.replace('.xlsx',  '.png'))
            double_bar_plot(name2, data)
    # except Exception as e:
    #     logger.error('3Interval_types  Problem found:', exc_info=True)
########################################################################################################
# This function returns the second group of data that we need to show, regarding third_columns_names2  #
########################################################################################################

def prepare_data_emphasised_scale_degrees_second(data: DataFrame, third_columns_names: List[str], third_columns_names2: List[str]):
    data2 = {}
    rest_data = set(third_columns_names) - set(third_columns_names2 + ['#7'])

    for name in third_columns_names2:
        column_data = []
        if name == '7':  # sumamos las columnas 7 y #7
            seven=[]
            if '7' in data.columns:
                seven = data[name]
            if '#7' in data.columns:
                hastagseven = data["#7"]
                column_data = [np.nansum([seven.tolist()[i], hastagseven.tolist()[
                                         i]]) for i in range(len(seven))]
            else:
                column_data = seven.tolist()
        elif name == "Others":  # sumamos todas las columnas de data menos 1, 4, 5, 7, #7
            column_data = data[rest_data].sum(axis=1).tolist()
        else:
            column_data = data[name].tolist()
        data2[name] = pd.Series(column_data)
    return data2

########################################################################
# Function to generate the files 4xEmphasised_scale_degrees.xlsx
########################################################################


def Emphasised_scale_degrees(datadata: DataFrame, sorting_list: list, name: str, results_path: str, sorting_lists: list, visualiser_lock: Lock, groups: list=None, additional_info=[]):
    try:
        workbook = openpyxl.Workbook()
        all_columns = data.columns.tolist()
        general_cols = copy.deepcopy(not_used_cols)
        for row in rows_groups:
            if len(rows_groups[row][0]) == 0:
                general_cols.append(row)
            else:
                general_cols += rows_groups[row][0]

        # nombres de todos los intervalos
        third_columns_names_origin = list(set(all_columns) - set(general_cols))
        third_columns_names_origin = sort(
            third_columns_names_origin, sorting_list)
        third_columns_names = ['Total analysed'] + third_columns_names_origin
        third_columns_names2 = ['Total analysed'] + \
            ['1', '4', '5', '7', 'Others']

        # esta sheet va de sumar, así que en todas las columnas el cómputo que hay que hacer es sumar!
        computations = ["sum"]*len(third_columns_names)
        computations2 = ["sum"]*len(third_columns_names2)

        emphdegrees = pd.DataFrame(prepare_data_emphasised_scale_degrees_second(
            data, third_columns_names, third_columns_names2))
        data2 = pd.concat(
            [data[[gc for gc in general_cols if gc in all_columns]], emphdegrees], axis=1)
        _, unique_columns = np.unique(data2.columns, return_index=True)
        data2 = data2.iloc[:, unique_columns]
        excel_sheet(workbook.create_sheet("Wheighted"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, last_column=True, last_column_average=False, average=True,
                     columns2=third_columns_names2,  data2=data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info, ponderate=True)
        excel_sheet(workbook.create_sheet("Horizontal Per"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, per=True, average=True, last_column=True, last_column_average=False,
                     columns2=third_columns_names2,  data2=data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info)
        excel_sheet(workbook.create_sheet("Vertical Per"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, per=True, average=False, last_column=True, last_column_average=True,
                     columns2=third_columns_names2,  data2=data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info)

        # Delete the default sheet
        if "Sheet" in workbook.get_sheet_names():
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        # with visualiser_lock:
        subtitile = 'in relation to the global key' if '4a' in name else 'in relation to the local key'
            # VISUALISATIONS
        if groups:
            data_grouped = data.groupby(list(groups))
            for g, datag in data_grouped:
                result_visualisations = path.join(
                    results_path, 'visualisations', g)
                if not os.path.exists(result_visualisations):
                    os.mkdir(result_visualisations)

                name1 = path.join(
                    result_visualisations, '4a.Scale_degrees_GlobalKey.png' if '4a' in name else '4b.scale_degrees_LocalKey.png')
                customized_plot(
                    name1, data, third_columns_names_origin, subtitile, second_title=g)
        else:
            name1 = path.join(results_path, 'visualisations',
                                '4a.scale_degrees_GlobalKey.png' if '4a' in name else '4b.scale_degrees_LocalKey.png')
            customized_plot(
                name1, data, third_columns_names_origin, subtitile)

    except Exception as e:
        logger.error('{}  Problem found:'.format(name), exc_info=True)


def Densities(data: DataFrame, results_path: str, name: str, sorting_lists: list, visualiser_lock: Lock, groups: list=None, additional_info: list=[]):
    try:
        workbook = openpyxl.Workbook()
        # Splitting the dataframes to reorder them
        data_general = data[metadata_columns + ['Total analysed']].copy()
        data = data[set(data.columns).difference(metadata_columns)]
        data_general = data_general.dropna(how='all', axis=1)
        data = data.dropna(how='all', axis=1)
        density_list = []
        notes_and_measures = []
        density_list = [
            i for i in data.columns if i.endswith('SoundingDensity')]
        density_df = data[density_list]
        notes_and_measures =[i for i in data.columns if i.endswith(
            'Measures') or i.endswith('Notes') or i.endswith('Mean')]

        notes_and_measures = data[notes_and_measures]

        density_df.columns = [i.replace('_','').replace('Part', '').replace(
            'Sounding', '').replace('Density', '').replace('Family', '').replace('Sound', '').replace('Notes', '') for i in density_df.columns]

        notes_and_measures.columns = [i.replace('_','').replace('Part', '').replace('SoundingMeasures', 'Measures').replace(
            'Sound', '').replace('Notes', '').replace('Mean', '').replace('Family', '') for i in notes_and_measures.columns]

        cols = sort(density_df.columns.tolist(), [
                    i.capitalize() for i in sorting_lists['InstrumentSorting']])
        
        density_df = density_df[cols]
        third_columns_names = density_df.columns.to_list()

        second_column_names = [("", 1), ("Density", len(third_columns_names))]
        third_columns_names.insert(0, 'Total analysed')
        data = pd.concat([data_general, density_df], axis=1)
        data_total = pd.concat([data_general, notes_and_measures], axis=1)

        computations = ["sum"] + ["mean"] * (len(third_columns_names)-1)
        computations2 = ["sum"] + ["mean_density"] * \
            (len(third_columns_names)-1)
        columns = third_columns_names
        excel_sheet(workbook.create_sheet("Weighted"), columns, data, third_columns_names, computations, sorting_lists, groups=groups, last_column=True,
                     last_column_average=True, second_columns=second_column_names, average=True, additional_info=additional_info, ponderate=False)
        excel_sheet(workbook.create_sheet("Horizontal"), columns, data_total, third_columns_names, computations2,  sorting_lists, groups=groups,
                     second_columns=second_column_names, per=False, average=True, last_column=True, last_column_average=True, additional_info=additional_info)

        # Deleting default sheet
        if "Sheet" in workbook.get_sheet_names():
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        # with visualiser_lock: #Apply when threads are usedwith visualizer_lock=threading.Lock()
        columns.remove('Total analysed')
        title = 'Instrumental densities'
        # VISUALISATIONS
        if groups:
            data_grouped = data.groupby(list(groups))
            for g, datag in data_grouped:
                result_visualisations = results_path + \
                    '\\visualisations\\' + str(g.replace('/', '_'))
                if not os.path.exists(result_visualisations):
                    os.mkdir(result_visualisations)
                name_bar = result_visualisations + \
                    '\\' + name.replace('.xlsx', '.png')
                bar_plot_extended(name_bar, datag, columns, 'Density',
                                  'Density', title, second_title=str(g))

        elif len(not_used_cols) == 5:  # 1 Factor. TODO: Try a different criteria
            groups = [i for i in rows_groups]
            exceptions_list = [ROLE, KEYSIGNATURE, TEMPO, YEAR, CITY, SCENE]
            for row in rows_groups:
                plot_name = name.replace(
                    '.xlsx', '') + '_Per_' + str(row.upper()) + '.png'
                name_bar = results_path + '\\visualisations\\' + plot_name
                if row not in not_used_cols:
                    if len(rows_groups[row][0]) == 0:  # no sub-groups
                        data_grouped = data.groupby(row, sort=True)
                        if data_grouped:
                            line_plot_extended(
                            name_bar, data_grouped, columns, 'Instrument', 'Density', title, second_title='Per ' + str(row))
                    else:
                        for i, subrow in enumerate(rows_groups[row][0]):
                            if subrow not in exceptions_list:
                                plot_name = name.replace(
                                    '.xlsx', '') + '_Per_' + str(row.upper()) + '_' + str(subrow) + '.png'
                                name_bar = results_path + '\\visualisations\\' + plot_name
                                data_grouped = data.groupby(subrow)
                                line_plot_extended(
                                    name_bar, data_grouped, columns, 'Instrument', 'Density', title, second_title= 'Per ' + str(subrow))
        else:
            name_bar = results_path + '\\visualisations\\' + \
                name.replace('.xlsx', '.png')
            bar_plot_extended(name_bar, data, columns,
                              'Density', 'Density', title)
    except Exception as e:
        logger.error('{}  Problem found:'.format(name), exc_info=True)
        print('Problem found in densities task: ', e)


def Textures(data: DataFrame, results_path: str, name: str, sorting_lists: list, visualiser_lock: Lock, groups: list=None, additional_info: list=[]):
    # try:
        workbook = openpyxl.Workbook()
        # Splitting the dataframes to reorder them
        data_general = data[metadata_columns + ['Total analysed']].copy()
        data_general = data_general.dropna(how='all', axis=1)
        notes_df = data[[i for i in data.columns if i.endswith('Notes') or i.endswith('Mean')]]
        
        textures_df = data[[c for c in data.columns if c.endswith('Texture')]]

        third_columns_names = []
        # Pre-treating data columns
        notes_df.columns = [i.replace('_', '').replace('Sound','').replace('Family','').replace('Part','').replace('Mean', '') for i in notes_df.columns]
        textures_df.columns = [i.replace('__Texture','').replace('__', '/').replace('Part', '') for i in textures_df.columns]
        
        for column in textures_df.columns:
            if column not in sorting_lists["TexturesSorting"]:
                textures_df.drop([column], axis=1, inplace=True)
            else:
                notes_df[column] = 0

        cols = sort(textures_df.columns.tolist(), sorting_lists['TexturesSorting'])

        textures_df = textures_df[cols]
        third_columns_names = textures_df.columns.to_list()

        second_column_names = [("", 1), ("Textures", len(third_columns_names))]
        third_columns_names.insert(0, 'Total analysed')
        second_column_names = [
            ("", 1), ("Texture", len(third_columns_names))]

        computations = ["sum"] + ["mean"] * (len(third_columns_names)-1)
        computations2 = ["sum"] + ["mean_texture"] * \
            (len(third_columns_names)-1)
        columns = third_columns_names

        data = pd.concat([data_general, textures_df], axis=1)
        notes_df = pd.concat([data_general, notes_df], axis=1)

        excel_sheet(workbook.create_sheet("Weighted_textures"), columns, data, third_columns_names, computations, sorting_lists, groups=groups,
                     last_column=True, last_column_average=True, second_columns=second_column_names, average=True, additional_info=additional_info, ponderate=False)
        excel_sheet(workbook.create_sheet("Horizontal_textures"), columns, notes_df, third_columns_names, computations2,  sorting_lists, groups=groups,
                     second_columns=second_column_names, per=False, average=True, last_column=True, last_column_average=True, additional_info=additional_info)

        # borramos la sheet por defecto
        if "Sheet" in workbook.get_sheet_names():
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        # with visualiser_lock:
        title = 'Textures'
        columns.remove('Total analysed')
        # VISUALISATIONS
        if groups:
            data_grouped = data.groupby(list(groups))
            for g, datag in data_grouped:
                result_visualisations = results_path + \
                    '\\visualisations\\' + str(g)
                if not os.path.exists(result_visualisations):
                    os.mkdir(result_visualisations)
                name_bar = result_visualisations + \
                    '\\' + name.replace('.xlsx', '.png')
                bar_plot_extended(
                    name_bar, datag, columns, 'Instrumental Textures', title, second_title=str(g))
        elif len(not_used_cols) == 5:  # 1 Factor. Try a different condition?
            groups = [i for i in rows_groups]
            exceptions_list = [ROLE, KEYSIGNATURE, TEMPO, YEAR, CITY, SCENE]
            for row in rows_groups:
                plot_name = name.replace(
                    '.xlsx', '') + '_Per_' + str(row.upper()) + '.png'
                name_bar = results_path + '\\visualisations\\' + plot_name
                if row not in not_used_cols:
                    if len(rows_groups[row][0]) == 0:  # no sub-groups
                        data_grouped = data.groupby(row, sort=True)
                        line_plot_extended(
                            name_bar, data_grouped, columns, 'Texture', 'Ratio', title, second_title='Per ' + str(row))
                    else:
                        for i, subrow in enumerate(rows_groups[row][0]):
                            if subrow not in exceptions_list:
                                plot_name = name.replace(
                                    '.xlsx', '') + '_Per_' + str(row.upper()) + '_' + str(subrow) + '.png'
                                name_bar = results_path + '\\visualisations\\' + plot_name
                                data_grouped = data.groupby(subrow)
                                line_plot_extended(
                                    name_bar, data_grouped, columns, 'Texture', 'Ratio', title, second_title='Per ' + str(subrow))
        else:
            name_bar = results_path + '\\visualisations\\' + \
                name.replace('.xlsx', '.png')
            bar_plot_extended(name_bar, data, columns,
                                'Instrumental Textures', 'Ratio', title)
    # except Exception as e:
    #     logger.error('{}  Problem found:'.format(name), exc_info=True)
