import os
from multiprocessing import Lock

import pandas as pd
from musif.common.constants import *
from musif.common.sort import sort, sort_columns
from musif.common.utils import get_color
from musif.config import Configuration
from musif.extract.features.harmony.constants import (ADDITIONS_prefix,
                                                      CHORD_prefix,
                                                      CHORD_TYPES_prefix,
                                                      CHORDS_GROUPING_prefix,
                                                      KEY_MODULATORY,
                                                      KEY_PERCENTAGE,
                                                      NUMERALS_prefix)
from musif.extract.features.harmony.utils import sort_labels
from musif.reports.constants import *
from musif.reports.utils import (Create_excel, get_excel_name,
                                 get_general_cols,
                                 save_workbook, print_basic_sheet)
import copy
from pandas.core.frame import DataFrame


def Harmonic_analysis(rows_groups: dict, not_used_cols: dict, factor, _cfg: Configuration, kwargs: DataFrame, pre_string, name: str, results_path: str, visualizations: Lock, additional_info: list=[], groups: list=None):
    try:
        workbook = openpyxl.Workbook()
        excel_name=get_excel_name(pre_string, name)
        general_cols = copy.deepcopy(not_used_cols)
        get_general_cols(rows_groups, general_cols)
        Print_Harmonic_Data(_cfg, kwargs['harmonic_data'], kwargs['common_df'], additional_info, groups, workbook)
        Print_Chords(factor, _cfg, kwargs['chords'], kwargs['common_df'],  groups, additional_info, workbook)
        Print_Functions(factor, _cfg, kwargs['functions'], kwargs['common_df'], groups, additional_info, workbook)
        Print_Keys(factor, _cfg, kwargs['key_areas'], kwargs['common_df'], groups, additional_info, workbook)
        save_workbook(os.path.join(results_path,excel_name), workbook, cells_size = NORMAL_WIDTH)
        
    except Exception as e:
        _cfg.write_logger.warn(get_color('WARNING')+'{}  Problem found: {}{}'.format(name, e, RESET_SEQ))

def Print_Harmonic_Data(_cfg, data, data_general, additional_info, groups, workbook):
    harmonic_rythm = [c for c in data.columns if 'Harmonic_rhythm' in c]
    chordTypes = [c.replace(CHORD_TYPES_prefix, '') for c in data.columns if CHORD_TYPES_prefix in c]
    chordTypes = sort(chordTypes, _cfg.sorting_lists['ChordTypeGrouppingSorting'])
    additions = [c for c in data.columns if ADDITIONS_prefix in c]

    data.columns=[i.replace(CHORD_TYPES_prefix, '').replace(NUMERALS_prefix, '') for i in data.columns]
        
    data = pd.concat((data_general, data[harmonic_rythm + chordTypes + additions]), axis=1)

    second_column = [("", 1), ('Harmonic Rhythm', len(harmonic_rythm)), ('Chord types', len(chordTypes)), ('Additions', len(additions))]
    third_columns = ['Total analysed'] + harmonic_rythm + chordTypes + additions
    
    print_basic_sheet(_cfg, "Harmonic data", data, additional_info, groups, workbook, second_column, third_columns)

def Print_Chords(factor, _cfg, data, data_general, groups, additional_info, workbook):
    data.columns=[i.replace(CHORDS_GROUPING_prefix, '') for i in data.columns]
    data.columns=[i.replace(CHORD_prefix, '') for i in data.columns]
    data.columns=[i.replace('_Count', '') for i in data.columns]
    try:
        data = sort_columns(data, sort_labels(data.columns, chordtype='occurrences')) #form=['', '+', 'o', '%', 'M']
    except:
        data = sort_columns(data, _cfg.sorting_lists['NumeralsSorting'])
    
    third_columns = data.columns.to_list()

    third_columns.insert(0, 'Total analysed')
    data = pd.concat([data_general, data], axis=1)

    computations = ["sum"] + ["mean"] * (len(third_columns)-1)

    Create_excel(workbook.create_sheet("Total Chords"), third_columns, data, third_columns, computations, _cfg.sorting_lists,
                     groups=groups, average=True,last_column=True, last_column_average=False, additional_info=additional_info, ponderate=True)
    if factor>=1:
        Create_excel(workbook.create_sheet("Chords Weighted"), third_columns, data, third_columns, computations, _cfg.sorting_lists,
                        groups=groups, per=True, average=True, last_column=True, last_column_average=False, additional_info=additional_info)

def Print_Keys(factor, _cfg, data, data_general, groups, additional_info, workbook):
    data1=data[[i for i in data.columns if KEY_MODULATORY in i]]
    data2=data[[i for i in data.columns if KEY_PERCENTAGE in i]]

    data1.columns=[i.replace(KEY_MODULATORY, '').replace('_', ' ') for i in data1.columns]
    data2.columns=[i.replace(KEY_PERCENTAGE, ' Percentage Measures').replace('_', ' ') for i in data2.columns]

    third_columns = ['Total analysed'] + data1.columns.tolist()
    third_columns2 = ['Total analysed'] + data2.columns.tolist()

    Print_Double_Excel('Key Areas', factor, _cfg, groups, additional_info, workbook, data_general, data1, data2, third_columns, third_columns2)

def Print_Functions(factor, _cfg, data, data_general, groups, additional_info, workbook):
    (data1, data2, data3, third_columns_names,
            third_columns_names2, third_columns_names3,
            second_column_names, second_column_names2,
            second_column_names3) = Process_data(data, NUMERALS_prefix, CHORDS_GROUPING_prefix, CHORDS_GROUPING_prefix,_cfg.sorting_lists['NumeralsSorting'],_cfg.sorting_lists['ModulationG2Sorting'],_cfg.sorting_lists['ModulationG2Sorting'])
    Print_Triple_Excel('Functions', factor, _cfg, groups, additional_info, workbook, data_general, data1, data2, data3, third_columns_names, third_columns_names2, third_columns_names3, second_column_names, second_column_names2, second_column_names3)

def Print_Triple_Excel(name, factor, _cfg, groups, additional_info, workbook, data_general, data1, data2, data3, third_columns_names, third_columns_names2, third_columns_names3, second_column_names, second_column_names2, second_column_names3):
    computations = ["sum"] + ['mean'] * (len(third_columns_names))
    computations2 = ['sum'] + ['mean'] * (len(third_columns_names2))
    computations3 = ['sum'] + ['mean'] * (len(third_columns_names3))

    data1 = pd.concat([data_general, data1], axis=1)
    data2 = pd.concat([data_general, data2], axis=1)
    data3 = pd.concat([data_general, data3], axis=1)

    Create_excel(workbook.create_sheet(name),
         third_columns_names, data1, third_columns_names, 
            computations, _cfg.sorting_lists, groups=groups, last_column=True, last_column_average=False, second_columns=second_column_names,
            data2=data2, columns2=third_columns_names2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, 
            data3=data3, columns3=third_columns_names3,  third_columns3=third_columns_names3, computations_columns3=computations3, second_columns3=second_column_names3,
            additional_info=additional_info, ponderate=False)
        
    if factor>=1:
        Create_excel(workbook.create_sheet(name + "_Horizontal"),
         third_columns_names, data1, third_columns_names,
          computations, _cfg.sorting_lists, groups=groups,data2=data2,
          last_column=True, last_column_average=False, second_columns=second_column_names,
                    columns2=third_columns_names2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, 
                    data3=data3, columns3=third_columns_names3,  third_columns3=third_columns_names3, computations_columns3=computations3, second_columns3=second_column_names3,
                additional_info=additional_info, ponderate=False)

def Print_Double_Excel(name, factor, _cfg, groups, additional_info, workbook, data_general, data1, data2, third_columns_names, third_columns_names2, second_column_names=None, second_column_names2=None):
    computations = ["sum"] + ['mean'] * (len(third_columns_names))    
    computations2 = ['sum'] + ['mean'] * (len(third_columns_names2))

    data1 = pd.concat([data_general, data1], axis=1)
    data2 = pd.concat([data_general, data2], axis=1)

    Create_excel(workbook.create_sheet(name),
         third_columns_names, data1, third_columns_names,
          computations, _cfg.sorting_lists, groups=groups,
            data2=data2,
            last_column=True, last_column_average=False, second_columns=second_column_names,
            columns2=third_columns_names2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, 
            additional_info=additional_info, ponderate=False)
        
    # if factor>=1:
    #     Create_excel(workbook.create_sheet(name + "_Horizontal"),
    #      third_columns_names, data1, third_columns_names,
    #       computations, _cfg.sorting_lists, groups=groups, data2 = data2,
    #       last_column=True, last_column_average=False, second_columns=second_column_names,
    #             columns2=third_columns_names2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, 
    #             additional_info=additional_info, ponderate=True)
                
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
    second_column_names3 = name_second_columns(third_columns_names3, prefix3+ ' 2')

    return data1, data2, data3, third_columns_names, third_columns_names2, third_columns_names3, second_column_names, second_column_names2, second_column_names3

def name_second_columns(third_columns_names, name):
    second_column_names = [("", 1), (name.replace('_', ''), len(third_columns_names))]
    return second_column_names

def insert_total_analysed(columns_names):
    columns_names.insert(0, 'Total analysed')
def SeparateDataframes(data):
    data_general = data[metadata_columns+ ['Total analysed']].copy()
    data = data[set(data.columns).difference(list(data_general.columns))]
    data = data.dropna(how='all', axis=1)
    data_general = data_general.dropna(how='all', axis=1)
    return data, data_general
