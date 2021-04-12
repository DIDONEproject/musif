import copy
import logging
import os
from os import path
from matplotlib.pyplot import axis

import numpy as np
import openpyxl
import pandas as pd
from musif.common.sort import sort

from .calculations import *
from .constants import *
from .visualisations import *

from musif.common.sort import sort_dataframe

if not os.path.exists(path.join(os.getcwd(), 'logs')):
    os.mkdir(path.join(os.getcwd(), 'logs'))

fh = logging.FileHandler(
    path.join(os.getcwd(), 'logs', 'generation.log'), 'w+')
fh.setLevel(logging.ERROR)
logger = logging.getLogger("generation")
logger.addHandler(fh)


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
########################################################################
# Function that finds the propper name used in our intermediate files  #
########################################################################


def columns_alike_our_data(third_columns_names, second_column_names, first_column_names=None):
    columns = []
    counter_first = 0
    sub_counter_first = 0
    counter_second = 0
    sub_counter_second = 0
    for c in third_columns_names:
        if first_column_names:
            cn = first_column_names[counter_first][0] + \
                second_column_names[counter_second][0] + c
            sub_counter_first += 1
            if sub_counter_first >= first_column_names[counter_first][1]:
                sub_counter_first = 0
                counter_first += 1
        else:
            cn = second_column_names[counter_second][0] + c
        sub_counter_second += 1
        if sub_counter_second >= second_column_names[counter_second][1]:
            sub_counter_second = 0
            counter_second += 1
        columns.append(cn)
    return columns
########################################################
# This function prints the names in the excell in bold
########################################################


def write_columns_titles(hoja, row, column, column_names):
    for c in column_names:
        hoja.cell(row, column).value = c
        hoja.cell(row, column).font = bold
        hoja.cell(row, column).fill = titles3Fill
        column += 1


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

# Voices splitting for duetos in Character classification


def split_voices(data):
    data = data.reset_index(drop=True)
    for ind in data.index:
        # if '&' in data['Role'][ind]:
        names = [i for i in data['Role'].tolist()]
        if '&' in str(names[ind]):
            voices = data['Role'][ind].split('&')
            pre_data = data.iloc[:ind]
            post_data = data.iloc[ind+1:]
            for i, _ in enumerate(voices):
                line = data.iloc[[ind]]
                line['Role'] = voices[i]
                line['Id'] = str(line['Id'].item()) + \
                    alfa[i] if str(line['Id'].item()) != '' else ''
                # line['Id']=str(line['Id'].item()) + alfa[i] if str(line['Id'].item()) != '' else ''
                line['Total analysed'] = 1/len(voices)
                line.iloc[:, line.columns.get_loc(
                    "Total analysed")+1:] = line.iloc[:, line.columns.get_loc("Total analysed")+1:].div(len(voices), axis=1)
                pre_data = pre_data.append(line, ignore_index=True)
            data = pre_data.append(post_data).reset_index(drop=True)

    return data

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
            extra_info = []
            if column_computation == 'mean_density':
                extra_info = subgroup_data[c+'Measures']
                value = compute_value(subgroup_data[c], column_computation, total_analysed_row,
                                      not_grouped_information, ponderate, extra_info=extra_info)  # absolute value

            elif column_computation == 'mean_texture':
                notes = subgroup_data['Notes' + c.split('/')[0]]
                subgroup_data[c] = notes
                notes_next = subgroup_data['Total notes ' + c.split('/')[1]]
                value = compute_value(subgroup_data[c], column_computation, total_analysed_row,
                                      not_grouped_information, ponderate, extra_info=notes_next)  # absolute value
            else:
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


##########################################################################################################
# Function in charge of printting the data, the arguments are the same as the explained in hoja_iValues  #
##########################################################################################################


def row_iteration(hoja, columns, row_number, column_number, data, third_columns, computations_columns, sorting_lists, group=None, first_columns=None, second_columns=None, per=False, average=False, last_column=False, last_column_average=False,
                  columns2=None, data2=None, third_columns2=None, computations_columns2=None, first_columns2=None, second_columns2=None, additional_info=[], ponderate=False):
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
                hoja.cell(row_number, column_number).value = "Per " + row
                hoja.cell(row_number, column_number).fill = yellowFill
                row_number += 1
                sorting = rows_groups[row][1]
                # 2. Write the information depending on the subgroups (ex: Geography -> City, Country)
                if len(rows_groups[row][0]) == 0:  # No subgroups
                    starting_row = row_number
                    # Sort the dataframe based on the json sorting_lists in Json_extra
                    data = sort_dataframe(data, row, sorting_lists, sorting)
                    groups_add_info, add_info = get_groups_add_info(
                        data, row, additional_info)
                    row_number, last_column_used = print_groups(hoja, data.groupby(groups_add_info, sort=False), row_number, column_number, columns, third_columns, computations_columns, first_columns, second_columns, per=per,
                                                                average=average, last_column=last_column, last_column_average=last_column_average, additional_info=add_info, ponderate=ponderate, not_grouped_df=(groups_add_info, data[groups_add_info + columns]))
                    if columns2 != None:  # Second subgroup
                        groups_add_info, add_info = get_groups_add_info(
                            data, row, additional_info)
                        if data2 is not None:
                            data2 = sort_dataframe(
                                data2, row, sorting_lists, sorting)
                        _, _ = print_groups(hoja, data.groupby(groups_add_info, sort=False) if data2 is None else data2.groupby(groups_add_info, sort=False), starting_row, last_column_used + 1, columns2, third_columns2, computations_columns2, first_columns2,
                                            second_columns2, per=per, average=average, last_column=last_column, last_column_average=last_column_average, additional_info=add_info, ponderate=ponderate, not_grouped_df=(groups_add_info, data[groups_add_info + columns]))
                else:  # has subgroups, ex: row = Date, subgroups: Year
                    if rows_groups[row][0] == ['Character', 'Role', 'Gender']:
                        data_joint = data.copy()
                        data = split_voices(data)
                    for i, subrows in enumerate(rows_groups[row][0]):
                        if (subrows == None or subrows not in forbiden) and subrows in all_columns:
                            if "Tempo" in subrows:
                                data[subrows] = data[subrows].fillna('')
                            starting_row = row_number
                            sort_method = sorting[i]
                            hoja.cell(
                                row_number, column_number).value = subrows
                            hoja.cell(
                                row_number, column_number).fill = greenFill
                            data = sort_dataframe(
                                data, subrows, sorting_lists, sort_method)

                            groups_add_info, add_info = get_groups_add_info(
                                data, subrows, additional_info)
                            row_number, last_column_used = print_groups(hoja, data.groupby(groups_add_info, sort=False), row_number, column_number, columns, third_columns, computations_columns, first_columns, second_columns, per=per,
                                                                        average=average, last_column=last_column, last_column_average=last_column_average, additional_info=add_info, ponderate=ponderate, not_grouped_df=(groups_add_info, data[groups_add_info + columns]))
                            if columns2 != None:  # Second subgroup
                                if "Tempo" in subrows and data2 is not None:
                                    data2[subrows] = data2[subrows].fillna('')
                                if data2 is not None:
                                    data2 = sort_dataframe(
                                        data2, subrows, sorting_lists, sort_method)
                                groups_add_info, add_info = get_groups_add_info(
                                    data, subrows, additional_info)
                                _, _ = print_groups(hoja, data.groupby(groups_add_info, sort=False) if data2 is None else data2.groupby(groups_add_info, sort=False), starting_row, last_column_used + 1, columns2, third_columns2, computations_columns2, first_columns2,
                                                    second_columns2, per=per, average=average, last_column=last_column, last_column_average=last_column_average, additional_info=add_info, ponderate=ponderate, not_grouped_df=(groups_add_info, data[groups_add_info + columns]))

                            row_number += 1
                    if rows_groups[row][0] == ['Role', 'RoleType', 'Gender']:
                        data = copy.deepcopy(data_joint)
                row_number += 1
    return row_number


def hoja_iValues(hoja, columns, data, third_columns, computations_columns, sorting_lists, groups=None, first_columns=None, second_columns=None, per=False, average=False, last_column=False, last_column_average=False,
                 columns2=None, data2=None, third_columns2=None, computations_columns2=None, first_columns2=None, second_columns2=None, additional_info=[], ponderate=False):

    row_number = 1  # we start writing in row 1
    column_number = 1
    if groups == None:
        row_iteration(hoja, columns, row_number, column_number, data, third_columns, computations_columns, sorting_lists, first_columns=first_columns, second_columns=second_columns, per=per,
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
                    hoja.cell(row_number, cnumber).value = g
                    hoja.cell(row_number, cnumber).fill = factors_Fill[i]
                    hoja.cell(row_number, cnumber).font = bold
                    counter_g = data[groups[i]].tolist().count(g)
                    hoja.cell(row_number, cnumber + 1).value = counter_g
                    if last_printed[i][0] != '':
                        hoja.merge_cells(
                            start_row=last_printed[i][1], start_column=i + 1, end_row=row_number - 2, end_column=i + 1)
                        hoja.cell(last_printed[i][1],
                                  i + 1).fill = factors_Fill[i]

                    last_printed[i] = (g, row_number + 1)

                row_number += 1
                cnumber += 1
            data2_grouped = None
            if data2 is not None:
                data2_grouped = data2.groupby(list(groups)).get_group(
                    group if len(group) > 1 else group[0])
            rn = row_iteration(hoja, columns, row_number, cnumber, group_data, third_columns, computations_columns, sorting_lists, group=groups, first_columns=first_columns, second_columns=second_columns, per=per,
                               average=average, last_column=last_column, last_column_average=last_column_average, columns2=columns2, data2=data2_grouped, third_columns2=third_columns2, computations_columns2=computations_columns2, first_columns2=first_columns2, second_columns2=second_columns2, additional_info=additional_info, ponderate=ponderate)
            row_number = rn
        # merge last cells
        for i, g in enumerate(group):
            if last_printed[i][0] == g:
                hoja.merge_cells(
                    start_row=last_printed[i][1], start_column=i + 1, end_row=row_number - 2, end_column=i + 1)
                hoja.cell(last_printed[i][1],  i + 1).fill = factors_Fill[i]

########################################################################
# Function ment to write the iValues excel
# -------
# data: all_info dataframe
# results_path: where to store the data
# name: name that the excel will take
# sorting lists: lists that will be used for sorting the results
# visualiser_lock: lock used to avoid deadlocks, as matplotlib is not thread safe
# additional info: columns additional to each
# remove_columns: used for factor 0, to avoid showing unusefull information
# groups: used for factor > 1
########################################################################


def iValues(data, results_path, name, sorting_lists, visualiser_lock, additional_info=[], remove_columns=False, groups=None):
    try:
        workbook = openpyxl.Workbook()

        # HOJA 1: STATISTICAL_VALUES
        column_names = ["Total analysed", "Intervallic ratio", "Trimmed intervallic ratio", "dif. Trimmed",
                        "% Trimmed", "Absolute intervallic ratio", "Std", "Absolute Std", 'Syllabic ratio']
        # HAREMOS LA MEDIA DE TODAS LAS COLUMNAS
        computations = ['sum'] + ["mean"]*(len(column_names) - 1)
        hoja_iValues(workbook.create_sheet("Statistical_values"), column_names, data, column_names, computations,
                     sorting_lists, groups=groups, average=True, additional_info=additional_info, ponderate=True)

        # HOJA 2: AMBITUS
        first_column_names = [("", 1), ("Lowest", 2), ("Highest", 2), ("Lowest", 2), ("Highest", 2), (
            "Ambitus", 8)] if not remove_columns else [("", 1), ("Lowest", 2), ("Highest", 2), ("Ambitus", 2)]

        second_column_names = [("", 5), ("Mean", 2), ("Mean", 2), ("Largest", 2), ("Smallest", 2), (
            "Absolute", 2), ("Mean", 2)] if not remove_columns else [("", 5), ("Largest", 2)]

        third_columns_names = ["Total analysed", "Note", "Index", "Note", "Index", "Note", "Index", "Note", "Index", "Semitones", "Interval", "Semitones", "Interval",
                               "Semitones", "Interval", "Semitones", "Interval"] if not remove_columns else ["Total analysed", "Note", "Index", "Note", "Index", "Semitones", "Interval"]

        computations = ["sum", "minNote", "min", "maxNote", "max", 'meanNote', 'mean', 'meanNote', 'mean', 'max', "maxInterval", 'min', "minInterval", 'absolute',
                        'absoluteInterval', "meanSemitones", "meanInterval"] if not remove_columns else ["sum", "minNote", "min", "maxNote", "max", 'max', "maxInterval"]

        columns = columns_alike_our_data(
            third_columns_names, second_column_names, first_column_names)

        hoja_iValues(workbook.create_sheet("Ambitus"), columns, data, third_columns_names, computations, sorting_lists, groups=groups,
                     first_columns=first_column_names, second_columns=second_column_names, average=True, additional_info=additional_info)

        # HOJA 3: LARGEST_LEAPS
        second_column_names = [("", 1), ("Ascending", 2), ("Descending", 2)]
        third_columns_names = ["Total analysed",
                               "Semitones", "Interval", "Semitones", "Interval"]
        columns = columns_alike_our_data(
            third_columns_names, second_column_names)
        computations = ["sum", "max", "maxInterval", "min", "minInterval"]

        hoja_iValues(workbook.create_sheet("Largest_leaps"), columns, data, third_columns_names, computations,
                     sorting_lists, groups=groups, second_columns=second_column_names, average=True, additional_info=additional_info)

        if "Sheet" in workbook.get_sheet_names():  # Delete the default sheet
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        with visualiser_lock:
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
            else:
                name_bar = results_path + \
                    path.join('visualisations', name.replace('.xlsx', '.png'))
                ivalues_bar_plot(name_bar, data, columns_visualisation)
                name_box = path.join(
                    results_path, 'visualisations', 'Ambitus' + name.replace('.xlsx', '.png'))
                box_plot(name_box, data)
    except Exception as e:
        logger.error('{}   Problem found:'.format(name), exc_info=True)


def iiaIntervals(data, name, sorting_list, results_path, sorting_lists, visualiser_lock, additional_info=[], groups=None):
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
        third_columns_names_origin = set(all_columns) - set(general_cols)
        third_columns_names_origin = sort(
            third_columns_names_origin, sorting_list)
        third_columns_names = ['Total analysed'] + third_columns_names_origin

        # esta hoja va de sumar, así que en todas las columnas el cómputo que hay que hacer es sumar!
        computations = ["sum"]*len(third_columns_names)

        hoja_iValues(workbook.create_sheet("Weighted"), third_columns_names, data, third_columns_names, computations, sorting_lists,
                     groups=groups, average=True, last_column=True, last_column_average=False, additional_info=additional_info, ponderate=True)
        hoja_iValues(workbook.create_sheet("Horizontal Per"), third_columns_names, data, third_columns_names, computations, sorting_lists,
                     groups=groups, per=True, average=True, last_column=True, last_column_average=False, additional_info=additional_info)
        hoja_iValues(workbook.create_sheet("Vertical Per"), third_columns_names, data, third_columns_names, computations, sorting_lists,
                     groups=groups, per=True, average=False, last_column=True, last_column_average=True, additional_info=additional_info)

        if "Sheet" in workbook.get_sheet_names():  # Delete the default sheet
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        with visualiser_lock:
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
    except Exception as e:
        logger.error('{}  Problem found:'.format(name), exc_info=True)

#########################################################
# Function to generate the file 3.Intervals_types.xlsx  #
#########################################################


def IIIIntervals_types(data, results_path, name, sorting_lists, visualiser_lock, groups=None, additional_info=[]):
    try:
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

        hoja_iValues(workbook.create_sheet("Weighted"), columns, data, third_columns_names, computations, sorting_lists, groups=groups, last_column=True, last_column_average=False, second_columns=second_column_names, average=True,
                     columns2=columns2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, additional_info=additional_info, ponderate=True)
        hoja_iValues(workbook.create_sheet("Horizontal Per"), columns, data, third_columns_names, computations, sorting_lists, groups=groups, second_columns=second_column_names, per=True, average=True, last_column=True, last_column_average=False,
                     columns2=columns2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, additional_info=additional_info)
        hoja_iValues(workbook.create_sheet("Vertical Per"), columns, data, third_columns_names, computations, sorting_lists, groups=groups, second_columns=second_column_names, per=True, average=False, last_column=True, last_column_average=True,
                     columns2=columns2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, additional_info=additional_info)

        # borramos la hoja por defecto
        if "Sheet" in workbook.get_sheet_names():
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        with visualiser_lock:
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
    except Exception as e:
        logger.error('3Interval_types  Problem found:', exc_info=True)
########################################################################################################
# This function returns the second group of data that we need to show, regarding third_columns_names2  #
########################################################################################################


def prepare_data_emphasised_scale_degrees_second(data, third_columns_names, third_columns_names2):
    data2 = {}
    rest_data = set(third_columns_names) - set(third_columns_names2 + ['#7'])

    for name in third_columns_names2:
        column_data = []
        if name == '7':  # sumamos las columnas 7 y #7
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

# Function to generate the files 4xEmphasised_scale_degrees.xlsx
########################################################################


def emphasised_scale_degrees(data, sorting_list, name, results_path, sorting_lists, visualiser_lock, groups=None, additional_info=[]):
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

        # esta hoja va de sumar, así que en todas las columnas el cómputo que hay que hacer es sumar!
        computations = ["sum"]*len(third_columns_names)
        computations2 = ["sum"]*len(third_columns_names2)

        emphdegrees = pd.DataFrame(prepare_data_emphasised_scale_degrees_second(
            data, third_columns_names, third_columns_names2))
        data2 = pd.concat(
            [data[[gc for gc in general_cols if gc in all_columns]], emphdegrees], axis=1)
        _, unique_columns = np.unique(data2.columns, return_index=True)
        data2 = data2.iloc[:, unique_columns]
        hoja_iValues(workbook.create_sheet("Wheighted"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, last_column=True, last_column_average=False, average=True,
                     columns2=third_columns_names2,  data2=data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info, ponderate=True)
        hoja_iValues(workbook.create_sheet("Horizontal Per"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, per=True, average=True, last_column=True, last_column_average=False,
                     columns2=third_columns_names2,  data2=data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info)
        hoja_iValues(workbook.create_sheet("Vertical Per"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, per=True, average=False, last_column=True, last_column_average=True,
                     columns2=third_columns_names2,  data2=data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info)

        # Delete the default sheet
        if "Sheet" in workbook.get_sheet_names():
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        with visualiser_lock:
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


def densities(data, results_path, name, sorting_lists, visualiser_lock, groups=None, additional_info=[]):
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
        notes_and_measures = [i for i in data.columns if i.endswith(
            'Measures') or i.endswith('Notes')]

        # for inst in [i for i in sorting_lists['InstrumentSorting']]:
        #     if inst.lower().startswith('vn'):
        #         # Add exception for violins
        #         col = 'Part' + inst[0].upper()+inst[1:] + 'SoundingDensity'
        #         if col in data.columns:
        #             density_list.append(col)
        #             notes_and_measures.append(
        #                 'Part' + inst[0].upper()+inst[1:] + 'Notes')
        #             notes_and_measures.append(
        #                 'Part' + inst[0].upper()+inst[1:] + 'SoundingMeasures')
        #     else:
        #         col = 'Sound' + inst[0].upper()+inst[1:] + 'SoundingDensity'
        #         if col in data.columns:
        #             density_list.append(col)
        #     if 'Sound' + inst[0].upper()+inst[1:] + 'Notes' in data.columns:
        #         notes_and_measures.append(
        #             'Sound' + inst[0].upper()+inst[1:] + 'Notes')
        #         notes_and_measures.append(
        #             'Sound' + inst[0].upper()+inst[1:] + 'SoundingMeasures')

        # density_df.drop('Total analysed', axis=1)
        notes_and_measures = data[notes_and_measures]

        density_df.columns = [i.replace('Part', '').replace(
            'Sounding', '').replace('Density', '').replace('Sound', '').replace('Notes', '') for i in density_df.columns]

        notes_and_measures.columns = [i.replace('Part', '').replace('SoundingMeasures', 'Measures').replace(
            'Sound', '').replace('Notes', '') for i in notes_and_measures.columns]

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
        hoja_iValues(workbook.create_sheet("Weighted"), columns, data, third_columns_names, computations, sorting_lists, groups=groups, last_column=True,
                     last_column_average=True, second_columns=second_column_names, average=True, additional_info=additional_info, ponderate=False)
        hoja_iValues(workbook.create_sheet("Horizontal"), columns, data_total, third_columns_names, computations2,  sorting_lists, groups=groups,
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

        elif len(not_used_cols) == 4:  # 1 Factor. TODO: Try a different condition?
            groups = [i for i in rows_groups]
            exceptions_list = ['Role', 'KeySignature', 'Tempo']
            for row in rows_groups:
                plot_name = name.replace(
                    '.xlsx', '') + '_Per_' + str(row.upper()) + '.png'
                name_bar = results_path + '\\visualisations\\' + plot_name
                if row not in not_used_cols:
                    if len(rows_groups[row][0]) == 0:  # no sub-groups
                        data_grouped = data.groupby(row, sort=True)
                        line_plot_extended(
                            name_bar, data_grouped, columns, 'Density', 'Density', title, second_title='Per ' + str(row))
                    else:
                        for i, subrow in enumerate(rows_groups[row][0]):
                            if subrow not in exceptions_list:
                                plot_name = name.replace(
                                    '.xlsx', '') + '_Per_' + str(row.upper()) + '_' + str(subrow) + '.png'
                                name_bar = results_path + '\\visualisations\\' + plot_name
                                data_grouped = data.groupby(subrow)
                                line_plot_extended(
                                    name_bar, data_grouped, columns, 'Density', 'Density', title, second_title='Per ' + str(subrow))
        else:
            name_bar = results_path + '\\visualisations\\' + \
                name.replace('.xlsx', '.png')
            bar_plot_extended(name_bar, data, columns,
                              'Density', 'Density', title)
    except Exception as e:
        logger.error('{}  Problem found:'.format(name), exc_info=True)
        print('Problem found in densities task')


def textures(data, results_path, name, sorting_lists, visualiser_lock, groups=None, additional_info=[]):
    try:
        workbook = openpyxl.Workbook()
        # Splitting the dataframes to reorder them
        data_general = data[metadata_columns + ['Total analysed']].copy()
        notes_df = data[set(data.columns).difference(data_general.columns)]
        data_general = data_general.dropna(how='all', axis=1)
        third_columns_names = []
        textures_df = pd.DataFrame()

        # if column not in sorting_lists["TextureSorting"] and not column.startswith('Total notes'):
        #         data.drop([column], axis=1, inplace=True)

        cols = sort(textures_df.columns.tolist(), [
                    i.capitalize() for i in sorting_lists['InstrumentSorting']])
        textures_df = textures_df[cols]
        third_columns_names = textures_df.columns.to_list()

        second_column_names = [("", 1), ("Textures", len(third_columns_names))]
        third_columns_names.insert(0, 'Total analysed')

        second_column_names = [
            ("", 1), ("Texture", len(third_columns_names))]

        # sorting_list = sorting_lists['TextureSorting']

        computations = ["sum"] + ["mean"] * (len(third_columns_names)-1)
        computations2 = ["sum"] + ["mean_texture"] * \
            (len(third_columns_names)-1)
        columns = third_columns_names
        hoja_iValues(workbook.create_sheet("Weighted_text"), columns, data, third_columns_names, computations, sorting_lists, groups=groups,
                     last_column=True, last_column_average=True, second_columns=second_column_names, average=True, additional_info=additional_info, ponderate=False)
        hoja_iValues(workbook.create_sheet("Horizontal_text"), columns, notes_df, third_columns_names, computations2,  sorting_lists, groups=groups,
                     second_columns=second_column_names, per=False, average=True, last_column=True, last_column_average=True, additional_info=additional_info)

        # borramos la hoja por defecto
        if "Sheet" in workbook.get_sheet_names():
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        with visualiser_lock:
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
            elif len(not_used_cols) == 4:  # 1 Factor. Try a different condition?
                groups = [i for i in rows_groups]
                exceptions_list = ['Role', 'KeySignature', 'Tempo']
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
    except Exception as e:
        logger.error('{}  Problem found:'.format(name), exc_info=True)
