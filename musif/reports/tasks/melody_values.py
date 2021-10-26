import os
from multiprocessing import Lock
from os import path

from music21 import interval
from pandas.core.frame import DataFrame

import musif.extract.features.lyrics as lyrics
from musif.common.constants import RESET_SEQ, get_color
from musif.config import Configuration
from musif.reports.constants import *
from musif.reports.utils import Create_excel, columns_alike_our_data, get_excel_name, save_workbook
from musif.reports.visualisations import box_plot, melody_bar_plot


def Melody_values(rows_groups, not_used_cols, factor, _cfg: Configuration, data: DataFrame, results_path: str, pre_string, name: str, visualiser_lock: Lock, additional_info: list=[], remove_columns: bool=False, groups: list=None):
    try:
        excel_name=get_excel_name(pre_string, name)
        workbook = openpyxl.Workbook()
        Rename_columns(data)
        data_general = data[metadata_columns+ ['Total analysed']].copy()

        PrintStatisticalValues(_cfg, data, additional_info, groups, workbook)
        PrintAmbitus(_cfg, data, data_general, additional_info, remove_columns, groups, workbook)
        PrintLargestLeaps(_cfg, data, data_general,additional_info, groups, workbook)

        save_workbook(os.path.join(results_path, excel_name), workbook, NORMAL_WIDTH)

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
                                    name_bar=name_bar.replace(IMAGE_EXTENSION,'')+'_'+subrow+IMAGE_EXTENSION
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

def PrintLargestLeaps(_cfg, data, data_general, additional_info, groups, workbook):
    second_column_names = [("", 1), ("Ascending", 2), ("Descending", 2)]
    third_columns_names = ["Total analysed",
                               "Semitones", "Interval", "Semitones", "Interval"]
    columns = columns_alike_our_data(
            third_columns_names, second_column_names)

    computations = ["sum", "max", "maxInterval", "min", "minInterval"]

    data.rename(columns={interval.LARGEST_ASC_INTERVAL: "AscendingInterval",interval.LARGEST_ASC_INTERVAL_SEMITONES: "AscendingSemitones", interval.LARGEST_DESC_INTERVAL: "DescendingInterval",
        interval.LARGEST_DESC_INTERVAL_SEMITONES: "DescendingSemitones"}, inplace=True)

    Create_excel(workbook.create_sheet("Largest_leaps"), columns, data, third_columns_names, computations,
                     _cfg.sorting_lists, groups=groups, second_columns=second_column_names, average=True, additional_info=additional_info)

def PrintAmbitus(_cfg, data, data_general, additional_info, remove_columns, groups, workbook):
    first_column_names = [("", 1), ("Lowest", 2), ("Highest", 2), ("Lowest", 2), ("Highest", 2), (
            "Ambitus", 6)] if not remove_columns else [("", 1), ("Lowest", 2), ("Highest", 2), ("Ambitus", 2)]

    second_column_names = [("", 5), ("Mean", 2), ("Mean", 2), ("Largest", 2), ("Smallest", 2), ("Mean", 2)] if not remove_columns else [("", 5), ("Largest", 2)]

    third_columns_names = ["Total analysed", "Note", "Index", "Note", "Index", "Note", "Index", "Note", "Index", "Semitones", "Interval", "Semitones", "Interval",
         "Semitones", "Interval"] if not remove_columns else ["Total analysed", "Note", "Index", "Note", "Index", "Semitones", "Interval"]

    computations = ["sum", "minNote", "min", "maxNote", "max", 'meanNote', 'mean', 'meanNote', 'mean', 'max', "maxInterval", 'min', "minInterval", 'absolute',
                        'absoluteInterval', "meanSemitones", "meanInterval"] if not remove_columns else ["sum", "minNote", "min", "maxNote", "max", 'max', "maxInterval"]

    columns = columns_alike_our_data(
            third_columns_names, second_column_names, first_column_names)
    columns=[i.replace('Ambitus', '') for i in columns]


    Create_excel(workbook.create_sheet("Ambitus"), columns, data, third_columns_names, computations, _cfg.sorting_lists, groups=groups,
                     first_columns=first_column_names, second_columns=second_column_names, average=True, additional_info=additional_info)

def PrintStatisticalValues(_cfg, data, additional_info, groups, workbook):
    column_names = ["Total analysed", "Intervallic mean", "Trimmed intervallic mean", "dif. Trimmed",
                        "% Trimmed", "Absolute intervallic ratio", "Std", "Absolute Std"]

    if lyrics.SYLLABIC_RATIO in data.columns:
        data.rename(columns={lyrics.SYLLABIC_RATIO: 'Syllabic ratio'}, inplace=True)
        column_names.append('Syllabic ratio')

    computations = ['sum'] + ["mean"]*(len(column_names) - 1)
    Create_excel(workbook.create_sheet("Statistical_values"), column_names, data, column_names, computations,
                    _cfg.sorting_lists, groups=groups, average=True, additional_info=additional_info, ponderate=True)

def Rename_columns(data):
    data['HighestMeanIndex']=data[ambitus.HIGHEST_NOTE_INDEX]
    data['LowestMeanIndex']=0.0
    data['HighestIndex']=0.0
    data['MeanSemitones']=0.0
    data['HighestIndex']=0.0
    data['LowestMeanNote']=0.0
    data['LowestIndex']=0.0
    data['HighestMeanNote']=0.0

    #Algo pasa coneste
    data['MeanInterval']=0.0

    data.rename(columns={interval.INTERVALLIC_MEAN: "Intervallic ratio", interval.TRIMMED_ABSOLUTE_INTERVALLIC_MEAN: "Trimmed intervallic ratio", interval.ABSOLUTE_INTERVALLIC_TRIM_DIFF: "dif. Trimmed",
                             interval.ABSOLUTE_INTERVALLIC_MEAN: "Absolute intervallic ratio", interval.INTERVALLIC_STD: "Std", interval.ABSOLUTE_INTERVALLIC_STD: "Absolute Std", interval.ABSOLUTE_INTERVALLIC_TRIM_RATIO: "% Trimmed"}, inplace=True)
    # data.rename(columns={ambitus.LOWEST_NOTE_INDEX: "LowestIndex", ambitus.HIGHEST_NOTE_INDEX: "HighestIndex", ambitus.HIGHEST_MEAN_INDEX: "HighestMeanIndex", ambitus.LOWEST_MEAN_INDEX: "LowestMeanIndex",
    #                      ambitus.LOWEST_NOTE: "LowestNote", ambitus.LOWEST_MEAN_NOTE: "LowestMeanNote", ambitus.HIGHEST_MEAN_NOTE: "HighestMeanNote", ambitus.LOWEST_MEAN_INDEX: "LowestMeanIndex", ambitus.HIGHEST_NOTE: "HighestNote"}, inplace=True)
    # data.rename(columns={ambitus.LOWEST_NOTE_INDEX: "LowestIndex", ambitus.HIGHEST_NOTE_INDEX: "HighestIndex",
    #                      ambitus.LOWEST_NOTE: "LowestNote",  ambitus.HIGHEST_NOTE: "HighestNote"}, inplace=True)
    
    data.columns=[i.replace('All', '') for i in data.columns]
