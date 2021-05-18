from pandas.core.frame import DataFrame
from typing import Dict, List
from openpyxl.writer.excel import ExcelWriter
from .constants import *

def get_groups_add_info(data: DataFrame, row: int, additional_info):
    if type(additional_info) == list:
        additional_info = [ai for ai in additional_info if ai in list(
            data.columns) and ai != row]
        groups = [row] + additional_info
        add_info = len(additional_info)
    else:  # It's a dictionary that indicates in which key it needs to be grouped with
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

def columns_alike_our_data(third_columns_names: List[str], second_column_names: List[str], first_column_names: List[str] = None):
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

def write_columns_titles(hoja: ExcelWriter, row: int, column: int, column_names: List[str]):
    for c in column_names:
        hoja.cell(row, column).value = c
        hoja.cell(row, column).font = bold
        hoja.cell(row, column).fill = titles3Fill
        column += 1


def print_averages_total(hoja: ExcelWriter, row: int, values:List, lable_column: int, values_column: list, average: bool=False, per: bool=False, exception: int=None):
    hoja.cell(row, lable_column).value = "Average" if average else "Total"
    hoja.cell(row, lable_column).fill = orangeFill

    for i, v in enumerate(values):
        if exception and i == exception:  # unicamente ocurre en % Trimmed en Melody_values
            hoja.cell(row, values_column).value = str(round(v * 100, 3)) + '%'
        else:
            hoja.cell(row, values_column).value = v if not per else str(v) + "%"
        values_column += 1


def print_averages_total_column(hoja: ExcelWriter, column: int, row: int, values:List, average: bool=False, per: bool=False):
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

def write_columns_titles_variable_length(hoja: ExcelWriter, row: int, column: int, column_names: List[str], fill:int):
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
def split_voices(data: DataFrame):
    data = data.reset_index(drop=True)
    for ind in data.index:
        names = [i for i in data[ROLE].tolist()]
        if '&' in str(names[ind]):
            voices = data[ROLE][ind].split('&')
            pre_data = data.iloc[:ind]
            post_data = data.iloc[ind+1:]
            for i, _ in enumerate(voices):
                line = data.iloc[[ind]]
                line[ROLE] = voices[i]
                line[ARIA_ID] = str(line[ARIA_ID].item()) + \
                    alfa[i] if str(line[ARIA_ID].item()) != '' else ''
                line['Total analysed'] = 1/len(voices)
                line.iloc[:, line.columns.get_loc(
                    "Total analysed")+1:] = line.iloc[:, line.columns.get_loc("Total analysed")+1:].div(len(voices), axis=1)
                pre_data = pre_data.append(line, ignore_index=True)
            data = pre_data.append(post_data).reset_index(drop=True)

    return data
