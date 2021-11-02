import copy
import os
from multiprocessing import Lock
from os import path

from pandas.core.frame import DataFrame

from musif.common.constants import RESET_SEQ, get_color
from musif.common.sort import sort
from musif.config import Configuration
from musif.reports.constants import *
from musif.reports.utils import Create_excel, columns_alike_our_data, get_excel_name, save_workbook
from musif.reports.visualisations import bar_plot, double_bar_plot, pie_plot


def Intervals(rows_groups: dict, not_used_cols: dict, factor, _cfg: Configuration, data: DataFrame, pre_string: str, name: str, sorting_list: list, results_path: str, visualizations: Lock, additional_info: list=[], groups: list=None):
    try:
        workbook = openpyxl.Workbook()
        all_columns = data.columns.tolist()
        general_cols = copy.deepcopy(not_used_cols)
        for row in rows_groups:
            if len(rows_groups[row][0]) == 0:
                general_cols.append(row)
            else:
                general_cols += rows_groups[row][0]

        third_columns_names_origin, third_columns_names = fix_column_names(sorting_list, all_columns, general_cols)
    
        computations = ["sum"]*len(third_columns_names)

        Create_excel(workbook.create_sheet("Weighted"), third_columns_names, data, third_columns_names, computations, _cfg.sorting_lists,
                     groups=groups, average=True, last_column=True, last_column_average=False, additional_info=additional_info, ponderate=True)
        if factor>=1:
            Create_excel(workbook.create_sheet("Horizontal Per"), third_columns_names, data, third_columns_names, computations, _cfg.sorting_lists,
                     groups=groups, per=True, average=True, last_column=True, last_column_average=False, additional_info=additional_info)

        save_workbook(os.path.join(results_path, get_excel_name(pre_string, name)), workbook, cells_size=NORMAL_WIDTH)

        if visualizations:
            if 'Clefs' in name:
                title = 'Use of clefs in the vocal part'
            elif name == 'Intervals_absolute':
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
                        result_visualisations, name.replace('.xlsx', IMAGE_EXTENSION))
                    bar_plot(name_bar, datag, third_columns_names_origin,
                                'Intervals' if 'Clef' not in name else 'Clefs', title, second_title=str(g))
            elif factor == 1:
                for row in rows_groups:
                    if row not in not_used_cols:
                        plot_name = name.replace(
                                '.xlsx', '') + '_Per_' + str(row.replace('Aria','').upper())
                        name_bar=path.join(results_path,'visualisations','Per_'+row.replace('Aria','').upper())
                        if not os.path.exists(name_bar):
                            os.makedirs(name_bar)

                        name_bar=path.join(name_bar,plot_name)

                        if len(rows_groups[row][0]) == 0:  # no subgroups
                            data_grouped = data.groupby(row, sort=True)
                            if data_grouped:
                                bar_plot(name_bar + IMAGE_EXTENSION, data_grouped, third_columns_names_origin,
                                            'Intervals' + '\n' + str(row).replace('Aria','').upper() if 'Clef' not in name else 'Clefs' + str(row).replace('Aria','').upper(), title)
                        else: #subgroups
                            for i, subrow in enumerate(rows_groups[row][0]):
                                if subrow not in EXCEPTIONS:
                                    data_grouped = data.groupby(subrow)
                                    bar_plot(name_bar+'_'+subrow + IMAGE_EXTENSION, data_grouped, third_columns_names_origin,
                                            'Intervals' + str(row).replace('Aria','').upper() if 'Clef' not in name else 'Clefs' + str(row).replace('Aria','').upper(), title)

            else:
                name_bar = path.join(
                    results_path, 'visualisations', name.replace('.xlsx', IMAGE_EXTENSION))
                bar_plot(name_bar, data, third_columns_names_origin,
                            'Intervals' if 'Clef' not in name else 'Clefs', title)
    except Exception as e:
        _cfg.write_logger.warn(get_color('WARNING')+'{} Problem found: {}{}'.format(name, e, RESET_SEQ))

def fix_column_names(sorting_list, all_columns, general_cols):
    third_columns_names_origin = set(all_columns) - set(general_cols)
    third_columns_names_origin = sort(
            third_columns_names_origin, sorting_list)
    third_columns_names = ['Total analysed'] + third_columns_names_origin
    return third_columns_names_origin,third_columns_names

def Intervals_types(rows_groups: dict, not_used_cols: dict, factor, _cfg: Configuration, data: DataFrame, results_path: str, pre_string: str, name: str, visualizations: Lock, groups=None, additional_info: list=[]):
    try:
        data.columns=[c.replace('Desc', 'Descending').replace('Asc', 'Ascending') for c in data.columns]
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

        Create_excel(workbook.create_sheet("Weighted"),
         columns, data, third_columns_names,
          computations, _cfg.sorting_lists, groups=groups, 
          last_column=True, last_column_average=False, second_columns=second_column_names,
           average=True, columns2=columns2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, additional_info=additional_info, ponderate=True)
        if factor>=1:
            Create_excel(workbook.create_sheet("Horizontal Per"), columns, data, third_columns_names, computations, _cfg.sorting_lists, groups=groups, second_columns=second_column_names, per=True, average=True, last_column=True, last_column_average=False,
                     columns2=columns2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, additional_info=additional_info)

        save_workbook(os.path.join(results_path, get_excel_name(pre_string, name)), workbook, cells_size=NORMAL_WIDTH)

        if visualizations:
            if groups:
                data_grouped = data.groupby(list(groups))
                for g, datag in data_grouped:
                    result_visualisations = path.join(
                        results_path, 'visualisations', g)
                    if not os.path.exists(result_visualisations):
                        os.mkdir(result_visualisations)

                    name_cakes = path.join(result_visualisations,
                                        name.replace('.xlsx',  '') + '_AD.png')
                    pie_plot(name_cakes, datag, second_title=str(g))
                    name_bars = path.join(result_visualisations,
                                        name.replace('.xlsx',  IMAGE_EXTENSION))
                    double_bar_plot(name_bars, data, second_title=str(g))

            elif factor == 1:
                for row in rows_groups:
                    name_folder=path.join(results_path,'visualisations','Per_'+row.replace('Aria','').upper())

                    name_cakes = name.replace(
                                '.xlsx', '').replace('1_factor','') + '_Per_' + str(row.replace('Aria','').upper())  + '_AD.png'
                    name_bars = name.replace('.xlsx',  '') + '_Per_' + str(row.replace('Aria','').upper()) + IMAGE_EXTENSION
                
                    if not os.path.exists(name_folder):
                        os.makedirs(name_folder)

                    name_cakes=path.join(name_folder,name_cakes)
                    name_bars=path.join(name_folder,name_bars)

                    
                    if row not in not_used_cols:
                        if len(rows_groups[row][0]) == 0:  # no sub-groups
                            data_grouped = data.groupby(row, sort=True)
                            if data_grouped:
                                # melody_bar_plot(name_bar, data_grouped, columns_visualisation, second_title='Per ' + str(subrow.replace('Aria','').upper()))

                                pie_plot(name_cakes, data_grouped, second_title='Per ' + str(row.replace('Aria','').upper()))
                                double_bar_plot(name_bars, data_grouped, 'Per ' + str(row.replace('Aria','').upper()))

                        else: #subgroups
                                for subrow in rows_groups[row][0]:
                                    if subrow not in EXCEPTIONS:
                                        name_cakes = path.join(results_path, 'visualisations',
                                        name.replace('.xlsx', '') + '_Per_' + str(row.upper()) + '_' + str(subrow) + '_AD.png')
                                        name_bars = path.join(results_path, 'visualisations',
                                        name.replace('.xlsx',  '') + '_Per_' + str(row.upper()) + '_' + str(subrow) + IMAGE_EXTENSION)

                                        data_grouped = data.groupby(subrow)
                                        pie_plot(name_cakes, data_grouped, second_title='Per ' + str(subrow.replace('Aria','').upper()))
                                        double_bar_plot(name_bars, data_grouped, 'Per ' + str(row.replace('Aria','').upper()))

            else:
                name_cakes = path.join(results_path, 'visualisations',
                                    name.replace('.xlsx', '') + '_AD.png')
                pie_plot(name_cakes, data)
                name_bars = path.join(results_path, 'visualisations',
                                    name.replace('.xlsx',  IMAGE_EXTENSION))
                double_bar_plot(name_bars, data)
    except Exception as e:
        _cfg.write_logger.warn(get_color('WARNING')+'{}  Problem found: {}{}'.format(name, e, RESET_SEQ))
