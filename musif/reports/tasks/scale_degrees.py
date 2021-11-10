import copy
import os
from multiprocessing import Lock
from os import path
from typing import List

import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame

from musif.common.constants import RESET_SEQ
from musif.common.sort import sort
from musif.common.utils import get_color
from musif.config import Configuration
from musif.reports.constants import *
from musif.reports.utils import Create_excel, get_excel_name, get_general_cols, save_workbook
from musif.reports.visualisations import customized_plot


########################################################################
# Function to generate the reports files Emphasised_scale_degrees.xlsx
########################################################################

def Emphasised_scale_degrees(rows_groups, not_used_cols, factor, _cfg: Configuration, data: DataFrame, pre_string, name: str, 
results_path: str, visualiser_lock: Lock, groups: list=None, additional_info=[]):
    try:
        workbook = openpyxl.Workbook()
        relative = True if 'relative' in name else False
        excel_name = get_excel_name(pre_string, name)
        if relative:
            data.columns=[i.replace('_relative','') for i in data.columns]

        all_columns = data.columns.tolist()
        general_cols = copy.deepcopy(not_used_cols)
        get_general_cols(rows_groups, general_cols)

        third_columns_names_origin = list(set(all_columns) - set(general_cols))
        third_columns_names_origin = sort(third_columns_names_origin, _cfg.sorting_lists["ScaleDegrees"])
        third_columns_names = ['Total analysed'] + third_columns_names_origin
        third_columns_names2 = ['Total analysed'] + \
            ['1','3', '4', '5', '7', 'Others']

        computations = ["sum"]*len(third_columns_names)
        computations2 = ["sum"]*len(third_columns_names2)

        emph_degrees = pd.DataFrame(prepare_data_emphasised_scale_degrees_second(
            data, third_columns_names, third_columns_names2))
        data2 = pd.concat(
            [data[[gc for gc in general_cols if gc in all_columns]], emph_degrees], axis=1)
        _, unique_columns = np.unique(data2.columns, return_index=True)
        data2 = data2.iloc[:, unique_columns]

        Create_excel(workbook.create_sheet("Weighted"), third_columns_names, data, third_columns_names, computations, _cfg.sorting_lists, groups=groups, last_column=True, last_column_average=False, average=True,
                     columns2=third_columns_names2,  data2=data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info, ponderate=True)
        
        # if factor>=1:
        #     Create_excel(workbook.create_sheet("Horizontal Per"), third_columns_names, data, third_columns_names, computations, _cfg.sorting_lists, groups=groups, per=True, average=True, last_column=True, last_column_average=False,
        #              columns2=third_columns_names2,  data2=data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info)

        save_workbook(os.path.join(results_path, excel_name) , workbook, cells_size=NARROW)

        # with visualiser_lock:
        Subtitle = 'in relation to the global key' if not relative else 'in relation to the local key'

            # VISUALISATIONS
        if groups:
            data_grouped = data.groupby(list(groups))
            for g, datag in data_grouped:
                result_visualisations = path.join(
                    results_path, 'visualisations', g)
                if not os.path.exists(result_visualisations):
                    os.mkdir(result_visualisations)

                name1 = path.join(
                    result_visualisations, 'Scale_degrees_GlobalKey.png' if not relative else 'Scale_degrees_LocalKey.png')
                customized_plot(
                    name1, data, third_columns_names_origin, Subtitle, second_title=g)
        else:
            name1 = path.join(results_path, 'visualisations',
                                'Scale_degrees_GlobalKey.png' if 'A' in name else 'Scale_degrees_LocalKey.png')
            customized_plot(
                name1, data, third_columns_names_origin, Subtitle)

    except Exception as e:
        _cfg.write_logger.warn(get_color('WARNING')+'{}  Problem found: {}{}'.format(name, e, RESET_SEQ))


########################################################################################################
# This function returns the second group of data that we need to show, regarding third_columns_names2  #
########################################################################################################

def prepare_data_emphasised_scale_degrees_second(data: DataFrame, third_columns_names: List[str], third_columns_names2: List[str]):
    data2 = {}
    rest_data = set(third_columns_names) - set(third_columns_names2 + ['#7'])

    for name in third_columns_names2:
        column_data = []
        if name == '7' and name in data:  # sumamos las columnas 7 y #7
            seven=[]
            if '7' in data.columns:
                seven = data[name]
            if '#7' in data.columns:
                hastagseven = data["#7"]
                column_data = [np.nansum([seven.tolist()[i], hastagseven.tolist()[
                                         i]]) for i in range(len(seven))]
            else:
                column_data = seven
        if name == '3' and name in data:  # sumamos las columnas 3 y 3b
            three=[]
            if '3' in data.columns:
                three = data[name]
            if 'b3' in data.columns:
                flat_3 = data["b3"]
                column_data = [np.nansum([three.tolist()[i], flat_3.tolist()[
                                         i]]) for i in range(len(three))]
            else:
                column_data = three

        elif name == "Others":  # sumamos todas las columnas de data menos 1, 4, 5, 7, #7
            column_data = data[rest_data].sum(axis=1).tolist()
        else:

            column_data = data[name].tolist() if name in data else 0

        data2[name] = pd.Series(column_data)
    return data2