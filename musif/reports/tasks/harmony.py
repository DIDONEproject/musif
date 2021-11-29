import copy
import os
from multiprocessing import Lock

import openpyxl
import pandas as pd
from musif.common.sort import sort_columns, sort_list
from musif.config import Configuration
from musif.extract.features.harmony.constants import (HARMONIC_RHYTHM,
                                                      HARMONIC_RHYTHM_BEATS,
                                                      KEY_MODULATORY,
                                                      KEY_PERCENTAGE,
                                                      ADDITIONS_prefix,
                                                      CHORD_prefix,
                                                      CHORD_TYPES_prefix,
                                                      CHORDS_GROUPING_prefix,
                                                      NUMERALS_prefix)
from .sort_labels import sort_labels
from musif.logs import pwarn
from musif.reports.constants import COMMON_DF, NORMAL_WIDTH
from musif.reports.utils import (Create_excel, get_excel_name,
                                 get_general_cols, print_basic_sheet,
                                 save_workbook)
from pandas.core.frame import DataFrame


def Harmonic_analysis(rows_groups: dict, not_used_cols: dict, factor, _cfg: Configuration, kwargs: DataFrame, pre_string, name: str, results_path: str, visualizations: Lock, additional_info: list=[], groups: list=None):
    try:
        workbook = openpyxl.Workbook()
        excel_name=get_excel_name(pre_string, name)
        general_cols = copy.deepcopy(not_used_cols)
        get_general_cols(rows_groups, general_cols)
        Print_Harmonic_Data(_cfg, kwargs, additional_info, groups, workbook)
        Print_Chords(factor, _cfg, kwargs,  groups, additional_info, workbook)
        Print_Functions(factor, _cfg, kwargs, groups, additional_info, workbook)
        Print_Keys(factor, _cfg, kwargs, groups, additional_info, workbook)
        save_workbook(os.path.join(results_path,excel_name), workbook, cells_size = NORMAL_WIDTH)
        
    except Exception as e:
        pwarn('{}  Problem found: {}'.format(name, e))
        
def Print_Harmonic_Data(_cfg, info, additional_info, groups, workbook):
    data=info['harmonic_data']
    harmonic_rythm = [c for c in data.columns if 'Harmonic_rhythm' in c]

    chordTypes = [c for c in data.columns if CHORD_TYPES_prefix in c]
    chordTypes = sort_list(chordTypes, _cfg.sorting_lists['ChordTypeGrouppingSorting'])

    additions = [c for c in data.columns if ADDITIONS_prefix in c]

    second_column = [("", 1), ('Harmonic Rhythm', len(harmonic_rythm)), ('Chord types', len(chordTypes)), ('Additions', len(additions))]
    
    data=data[harmonic_rythm + chordTypes + additions]

    data.columns=[i.replace(CHORD_TYPES_prefix, '').replace(NUMERALS_prefix, '').replace(ADDITIONS_prefix,'') for i in data]
    data.rename(columns={HARMONIC_RHYTHM: 'Bars', HARMONIC_RHYTHM_BEATS: 'Beats'}, inplace=True)
    data_total = pd.concat((info[COMMON_DF], data), axis=1)
        
    third_columns = ['Total analysed'] + list(data.columns)
    
    print_basic_sheet(_cfg, "Harmonic data", data_total, additional_info, groups, workbook, second_column, third_columns)

def Print_Chords(factor, _cfg, info, groups, additional_info, workbook):
    data=info['chords']
    data.columns=[i.replace(CHORDS_GROUPING_prefix, '') for i in data.columns]
    data.columns=[i.replace(CHORD_prefix, '') for i in data.columns]
    data.columns=[i.replace('_Count', '') for i in data.columns]
    try:
        data = sort_columns(data, sort_labels(data.columns, chordtype='occurrences',form=['', '+', 'o', '%', 'M']))
    except:
        data = sort_columns(data, _cfg.sorting_lists['NumeralsSorting'])
    
    third_columns = data.columns.to_list()

    third_columns.insert(0, 'Total analysed')
    data = pd.concat([info[COMMON_DF], data], axis=1)

    computations = ["sum"] + ["mean"] * (len(third_columns)-1)

    Create_excel(workbook.create_sheet("Chords Weighted"), third_columns, data, third_columns, computations, _cfg.sorting_lists,
                        groups=groups, per=True, average=True, last_column=True, last_column_average=False, additional_info=additional_info)

def Print_Keys(factor, _cfg, info, groups, additional_info, workbook):
    data=info['key_areas']
    data1=data[[i for i in data.columns if KEY_MODULATORY in i]]
    data2=data[[i for i in data.columns if KEY_PERCENTAGE in i]]

    data1.columns=[i.replace(KEY_MODULATORY, '').replace('Key','').replace('_', ' ') for i in data1.columns]
    data2.columns=[i.replace(KEY_PERCENTAGE, '').replace('Key','').replace('_', ' ') for i in data2.columns]
    
    third_columns = ['Total analysed'] + data1.columns.tolist()
    third_columns2 = ['Total analysed'] + data2.columns.tolist()
    
    second_columns = [("", 1), ('No.', len(third_columns))]
    second_columns2 = [("", 1), ('Measures', len(third_columns2))]
    
    Print_Double_Excel('Key Areas', factor, _cfg, groups, additional_info, workbook, info[COMMON_DF], data1, data2, third_columns, third_columns2, second_column_names=second_columns, second_column_names2=second_columns2)

def Print_Functions(factor, _cfg, info, groups, additional_info, workbook):
    data=info['functions']
    (data1, data2, data3, third_columns_names,
            third_columns_names2, third_columns_names3,
            second_column_names, second_column_names2,
            second_column_names3) = Process_data(data, NUMERALS_prefix, CHORDS_GROUPING_prefix, CHORDS_GROUPING_prefix,_cfg.sorting_lists['NumeralsSorting'],_cfg.sorting_lists['ModulationG2Sorting'],_cfg.sorting_lists['ModulationG2Sorting'])
    
    Print_Triple_Excel('Functions', factor, _cfg, groups, additional_info, workbook, info[COMMON_DF], data1, data2, data3, third_columns_names, third_columns_names2, third_columns_names3, second_column_names, second_column_names2, second_column_names3)

def Print_Triple_Excel(name, factor, _cfg, groups, additional_info, workbook, data_general, data1, data2, data3, third_columns_names, third_columns_names2, third_columns_names3, second_column_names, second_column_names2, second_column_names3):
    computations = ["sum"] + ['mean'] * (len(third_columns_names))
    computations2 = ['sum'] + ['mean'] * (len(third_columns_names2))
    computations3 = ['sum'] + ['mean'] * (len(third_columns_names3))

    data1 = pd.concat([data_general, data1], axis=1)
    data2 = pd.concat([data_general, data2], axis=1)
    data3 = pd.concat([data_general, data3], axis=1)

    Create_excel(workbook.create_sheet(name + " Weighted"),
        third_columns_names, data1, third_columns_names,
        computations, _cfg.sorting_lists, groups=groups,
        data2=data2, second_columns=second_column_names,
        columns2=third_columns_names2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, 
        data3=data3, columns3=third_columns_names3,  third_columns3=third_columns_names3, computations_columns3=computations3, second_columns3=second_column_names3,
            additional_info=additional_info, per=True, average=True, last_column=True, last_column_average=False,)

def Print_Double_Excel(name, factor, _cfg, groups, additional_info, workbook, data_general, data1, data2, third_columns_names, third_columns_names2, second_column_names=None, second_column_names2=None):
    computations = ["sum"] + ['mean'] * (len(third_columns_names))    
    computations2 = ['sum'] + ['mean'] * (len(third_columns_names2))

    data1 = pd.concat([data_general, data1], axis=1)
    data2 = pd.concat([data_general, data2], axis=1)

    Create_excel(workbook.create_sheet(name),
        third_columns_names, data1, third_columns_names,
        computations, _cfg.sorting_lists, groups=groups,
        second_columns=second_column_names,
        data2=data2, columns2=third_columns_names2, third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2,
        additional_info=additional_info, per=True, average=True, last_column=True, last_column_average=False)

def Process_data(data, prefix1, prefix2, prefix3, sorting_list1, sorting_list2, sorting_list3):
    data.columns= [i.replace('_Count','') for i in data.columns]
    data1 = data[[i for i in data.columns if prefix1 in i]]
    data1.columns = [i.replace(prefix1,'').replace('_',' ') for i in data1.columns]

    data2 = data[[i for i in data.columns if prefix2 + '1' in i]]
    data2.columns = [i.replace(prefix2 + '1','').replace('_',' ') for i in data2.columns]

    data3 = data[[i for i in data.columns if prefix2 + '2' in i]]
    data3.columns = [i.replace(prefix3 + '2', 'Grouped').replace('_',' ') for i in data3.columns]

    data1 = sort_columns(data1, sorting_list1)
    data2 = sort_columns(data2, sorting_list2)
    data3 = sort_columns(data3, sorting_list3)

    data2=data2.round(decimals =2)
    data3=data3.round(decimals =2)
        
    third_columns_names=list(data1.columns)
    third_columns_names2=list(data2.columns)
    third_columns_names3=list(data3.columns)
        
    insert_total_analysed(third_columns_names)
    insert_total_analysed(third_columns_names2)
    insert_total_analysed(third_columns_names3)

    second_column_names = name_second_columns(third_columns_names,prefix1)
    second_column_names2 = name_second_columns(third_columns_names2, prefix2)
    second_column_names3 = name_second_columns(third_columns_names3, prefix3 + ' 2')

    return data1, data2, data3, third_columns_names, third_columns_names2, third_columns_names3, second_column_names, second_column_names2, second_column_names3

def name_second_columns(third_columns_names, name):
    second_column_names = [("", 1), (name.replace('_', ''), len(third_columns_names))]
    return second_column_names

def insert_total_analysed(columns_names):
    columns_names.insert(0, 'Total analysed')