from typing import Dict, List
import os
from openpyxl.writer.excel import ExcelWriter
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame

from .constants import *

def adjust_excel_width_height(workbook: ExcelWriter):
            #Adjust columns width
        for sheet in workbook.worksheets:
            col_range = sheet[sheet.min_column : sheet.max_column]
            for col in range(1, len(col_range)):
                sheet.column_dimensions[get_column_letter(col)].width = 18

            row_range = sheet[sheet.min_row : sheet.max_row]
            for row in range(1, len(row_range)):
                sheet.row_dimensions[row].height = 20

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

def write_columns_titles(sheet: ExcelWriter, row: int, column: int, column_names: List[str]):
    for c in column_names:
        sheet.cell(row, column).value = c
        sheet.cell(row, column).font =  Font(size = 12, bold = True, name='Garamond')
        sheet.cell(row, column).fill = titles3Fill
        column += 1


def print_averages_total(sheet: ExcelWriter, row: int, values:List, lable_column: int, values_column: list, average: bool=False, per: bool=False, exception: int=None):
    sheet.cell(row, lable_column).value = "Average" if average else "Total"
    sheet.cell(row, lable_column).font =  Font(size = 12, bold = True, name='Garamond')
    sheet.cell(row, lable_column).fill = orangeFill

    for i, v in enumerate(values):
        if exception and i == exception:  # unicamente ocurre en % Trimmed en Melody_values
            sheet.cell(row, values_column).value = str(round(v * 100, 3)).replace(',','.') + '%'
        else:
            sheet.cell(row, values_column).value = str(v).replace(',','.') if not per else str(v).replace(',','.') + "%"
        values_column += 1


def print_averages_total_column(sheet: ExcelWriter, row: int, column: int, values:List, average: bool=False, per: bool=False):
    sheet.cell(row, column).value = "Average" if average else "Total"
    sheet.cell(row, column).font =  Font(size = 12, bold = True, name='Garamond')
    sheet.cell(row, column).fill = orangeFill
    row += 1
    for v in values:
        sheet.cell(row, column).value = str(v).replace(',','.') if not per else str(v).replace(',','.') + "%"
        row += 1

################################################################################################################
# This function prints a row with the column names with variable size (each name can use more than one column) #
# Column_names will be a list of tuples (name, length)                                                         #
################################################################################################################

def write_columns_titles_variable_length(sheet: ExcelWriter, row: int, column: int, column_names: List[str], fill:int):
    for c in column_names:
        sheet.cell(row, column).value = c[0]
        sheet.cell(row, column).font = BOLD
        if c[0] != '':
            sheet.cell(row, column).fill = fill
        sheet.cell(row, column).alignment = center
        sheet.merge_cells(start_row=row, start_column=column,
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

def remove_folder_contents(path: str):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            remove_folder_contents(file_path)

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
