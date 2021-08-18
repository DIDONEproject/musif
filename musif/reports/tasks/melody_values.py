### MELODY ###

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
from multiprocessing import Lock
import os
from os import path

import musif.extract.features.ambitus as ambitus
import musif.extract.features.lyrics as lyrics
import openpyxl
from config import Configuration
from music21 import interval
from musif.common.constants import get_color
from musif.reports.constants import *
from musif.reports.utils import (adjust_excel_width_height,
                                 columns_alike_our_data)
from musif.reports.visualisations import box_plot, melody_bar_plot
from pandas.core.frame import DataFrame
from musif.reports.report_generation import excel_sheet

def Melody_values(rows_groups, not_used_cols, factor, _cfg: Configuration, data: DataFrame, results_path: str, name: str, visualiser_lock: Lock, additional_info: list=[], remove_columns: bool=False, groups: list=None):
    try:
        workbook = openpyxl.Workbook()
        data.rename(columns={interval.INTERVALLIC_MEAN: "Intervallic ratio", interval.TRIMMED_ABSOLUTE_INTERVALLIC_MEAN: "Trimmed intervallic ratio", interval.ABSOLUTE_INTERVALLIC_TRIM_DIFF: "dif. Trimmed",
                             interval.ABSOLUTE_INTERVALLIC_MEAN: "Absolute intervallic ratio", interval.INTERVALLIC_STD: "Std", interval.ABSOLUTE_INTERVALLIC_STD: "Absolute Std", interval.ABSOLUTE_INTERVALLIC_TRIM_RATIO: "% Trimmed"}, inplace=True)
        data.rename(columns={ambitus.LOWEST_INDEX: "LowestIndex", ambitus.HIGHEST_INDEX: "HighestIndex", ambitus.HIGHEST_MEAN_INDEX: "HighestMeanIndex", ambitus.LOWEST_MEAN_INDEX: "LowestMeanIndex",
             ambitus.LOWEST_NOTE: "LowestNote", ambitus.LOWEST_MEAN_NOTE: "LowestMeanNote",ambitus.HIGHEST_MEAN_NOTE: "HighestMeanNote", ambitus.LOWEST_MEAN_INDEX: "LowestMeanIndex",ambitus.HIGHEST_NOTE: "HighestNote" }, inplace=True)
        # HOJA 1: STATISTICAL_VALUES
        column_names = ["Total analysed", "Intervallic ratio", "Trimmed intervallic ratio", "dif. Trimmed",
                        "% Trimmed", "Absolute intervallic ratio", "Std", "Absolute Std"]

        if lyrics.SYLLABIC_RATIO in data.columns:
            data.rename(columns={lyrics.SYLLABIC_RATIO: 'Syllabic ratio'}, inplace=True)
            column_names.append('Syllabic ratio')

        # HAREMOS LA MEDIA DE TODAS LAS COLUMNAS
        computations = ['sum'] + ["mean"]*(len(column_names) - 1)
        excel_sheet(workbook.create_sheet("Statistical_values"), column_names, data, column_names, computations,
                    _cfg.sorting_lists, groups=groups, average=True, additional_info=additional_info, ponderate=True)

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

        excel_sheet(workbook.create_sheet("Ambitus"), columns, data, third_columns_names, computations, _cfg.sorting_lists, groups=groups,
                     first_columns=first_column_names, second_columns=second_column_names, average=True, additional_info=additional_info)

        # HOJA 3: LARGEST_LEAPS
        second_column_names = [("", 1), ("Ascending", 2), ("Descending", 2)]
        third_columns_names = ["Total analysed",
                               "Semitones", "Interval", "Semitones", "Interval"]
        columns = columns_alike_our_data(
            third_columns_names, second_column_names)

        computations = ["sum", "max", "maxInterval", "min", "minInterval"]

        data.rename(columns={interval.LARGEST_ASC_INTERVAL: "AscendingInterval",interval.LARGEST_ASC_INTERVAL_SEMITONES: "AscendingSemitones", interval.LARGEST_DESC_INTERVAL: "DescendingInterval",interval.LARGEST_DESC_INTERVAL_SEMITONES: "DescendingSemitones"}, inplace=True)

        excel_sheet(workbook.create_sheet("Largest_leaps"), columns, data, third_columns_names, computations,
                     _cfg.sorting_lists, groups=groups, second_columns=second_column_names, average=True, additional_info=additional_info)

        if "Sheet" in workbook.get_sheet_names():  # Delete the default sheet
            std = workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)

        adjust_excel_width_height(workbook)


        workbook.save(os.path.join(results_path, name))

        # with visualiser_lock:
        # VISUALISATIONS
        columns_visualisation = [
            'Intervallic ratio', 'Trimmed intervallic ratio',  'Std', "Absolute intervallic ratio","Absolute Std"]
        if groups:
            data_grouped = data.groupby(list(groups))
            for g, datag in data_grouped:
                result_visualisations = os.path.join(
                    results_path, 'visualisations', g)
                if not os.path.exists(result_visualisations):
                    os.mkdir(result_visualisations)

                name_bar = os.path.join(
                    result_visualisations, name.replace('.xlsx', IMAGE_EXTENSION))
                melody_bar_plot(
                    name_bar, datag, columns_visualisation, second_title=str(g))
                name_box = path.join(
                    result_visualisations, 'Ambitus' + name.replace('.xlsx', IMAGE_EXTENSION))
                box_plot(name_box, datag, second_title=str(g))

        elif factor == 1:
            # groups = [i for i in rows_groups]
            for row in rows_groups:
                plot_name = name.replace(
                    '.xlsx', '') + '_Per_' + str(row.replace('Aria','').upper()) + IMAGE_EXTENSION
                name_bar =path.join(results_path,'visualisations','Per_'+row.replace('Aria','').upper())
                if not os.path.exists(name_bar):
                    os.makedirs(name_bar)
                name_bar=path.join(name_bar,plot_name)
                if row not in not_used_cols:
                    if len(rows_groups[row][0]) == 0:  # no sub-groups
                        data_grouped = data.groupby(row, sort=True)
                        if data_grouped:
                            melody_bar_plot(name_bar, data_grouped, columns_visualisation, second_title='Per ' + str(row.replace('Aria','').upper()))
                            if row == CLEF1: #Exception for boxplots
                                name_box = name_bar.replace('Melody_Values', 'Ambitus')
                                box_plot(name_box, data_grouped, second_title='Per '+ str(row.replace('Aria','').upper()))
                    else: #subgroups
                            for i, subrow in enumerate(rows_groups[row][0]):
                                if subrow not in EXCEPTIONS:
                                    plot_name = name.replace(
                                        '.xlsx', '') + '_Per_' + str(row.upper()) + '_' + str(subrow) + IMAGE_EXTENSION
                                    name_bar = results_path + '\\visualisations\\' + plot_name
                                    data_grouped = data.groupby(subrow)
                                    melody_bar_plot(name_bar, data_grouped, columns_visualisation, second_title='Per ' + str(subrow.replace('Aria','').upper()))
                                    name_box = path.join(
                                    results_path, 'visualisations', 'Ambitus' + name.replace('.xlsx', IMAGE_EXTENSION))
                                    
                                    if subrow == ROLE:
                                        box_plot(name_box, data_grouped, second_title='Per '+ str(subrow.replace('Aria','').upper()))
        else:                   
            name_bar = path.join(results_path,path.join('visualisations', name.replace('.xlsx', IMAGE_EXTENSION)))
            melody_bar_plot(name_bar, data, columns_visualisation)
            name_box = path.join(
                results_path, 'visualisations', 'Ambitus' + name.replace('.xlsx', IMAGE_EXTENSION))
            box_plot(name_box, data)
    except Exception as e:
        _cfg.write_logger.warn(get_color('WARNING')+'{}  Problem found: {}{}'.format(name, e, RESET_SEQ))
