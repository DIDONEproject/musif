import os
from multiprocessing import Lock

import pandas as pd
from musif.common.constants import *
from musif.common.sort import sort, sort_columns
from musif.config import Configuration
from musif.extract.features.custom.__constants import (KEY_GROUPING,
                                                       ADDITIONS_prefix,
                                                       CHORD_prefix,
                                                       CHORD_TYPES_prefix,
                                                       CHORDS_GROUPING_prefix,
                                                       KEY_prefix,
                                                       NUMERALS_prefix)
from musif.reports.constants import *
from musif.reports.utils import (Create_excel, get_excel_name,
                                 get_general_cols, remove_underscore,
                                 save_workbook)
from numpy import copy
from pandas.core.frame import DataFrame

from ..harmony_sorting import *  # TODO: REVIEW

<<<<<<< HEAD

=======
>>>>>>> 7892977 (harmony fixings and report)
def Harmonic_data(rows_groups: dict, not_used_cols: dict, factor, _cfg: Configuration, data: DataFrame, pre_string, name: str, results_path: str, visualiser_lock: Lock, additional_info: list=[], groups: list=None):
    try:
        additions=[]
        workbook = openpyxl.Workbook()
        excel_name=get_excel_name(pre_string, name)
        general_cols = copy.deepcopy(not_used_cols)
        data_general = data[metadata_columns+ ['Total analysed']].copy()
        get_general_cols(rows_groups, general_cols)

        harmonic_rythm = [c for c in data.columns if 'Harmonic_rhythm' in c]
        chordTypes = [c.replace(CHORD_TYPES_prefix, '') for c in data.columns if CHORD_TYPES_prefix in c]
        chordTypes = sort(chordTypes, _cfg.sorting_lists['ChordTypeGrouppingSorting'])

        # additions = [c.replace(ADDITIONS_prefix, '') for c in data.columns if ADDITIONS_prefix in c]

        numerals = [c.replace(NUMERALS_prefix, '') for c in data.columns if NUMERALS_prefix in c]
        numerals = sort(numerals, _cfg.sorting_lists['NumeralsSorting'])

        #Remove prefixes
        data.columns=[i.replace(CHORD_TYPES_prefix, '').replace(ADDITIONS_prefix, '').replace(NUMERALS_prefix, '') for i in data.columns]
        
        data=pd.concat((data_general,data[harmonic_rythm+numerals + chordTypes]), axis=1)
        data = data.round(decimals = 2)


        second_column_names = [("", 1),('Harmonic Rhythm', len(harmonic_rythm)), ('Numerals', len(numerals)), ('Chord types', len(chordTypes))]
        #  ('Additions', len(additions))]
        

        third_columns_names = ['Total analysed'] + harmonic_rythm + additions + numerals + chordTypes

        columns = remove_underscore(third_columns_names)


        computations = ["sum"]+ ["mean"]*(len(third_columns_names) - 1)

        Create_excel(workbook.create_sheet("Weighted"), third_columns_names, data, columns, computations, _cfg.sorting_lists,
                    second_columns=second_column_names,
                    groups=groups, per = False, average=True, last_column=False, last_column_average=False, additional_info=additional_info)
        
        save_workbook(os.path.join(results_path,excel_name), workbook, NORMAL_WIDTH)
        
        # with visualiser_lock:
        # VISUALISATIONS
        title = 'Harmonic Data'
        # if groups:
        #     data_grouped = data.groupby(list(groups))
        #     for g, datag in data_grouped:
        #         result_visualisations = path.join(
        #             results_path, 'visualisations', g)
        #         if not os.path.exists(result_visualisations):
        #             os.mkdir(result_visualisations)
        #         name_bar = path.join(
        #             result_visualisations, name.replace('.xlsx', IMAGE_EXTENSION))
        #         bar_plot(name_bar, datag, third_columns_names_origin,
        #                     'Intervals' if 'Clef' not in name else 'Clefs', title, second_title=str(g))
        # elif factor == 1:
        #     for row in rows_groups:
        #         if row not in not_used_cols:
        #             plot_name = name.replace(
        #                     '.xlsx', '') + '_Per_' + str(row.replace('Aria','').upper())
        #             name_bar=path.join(results_path,'visualisations','Per_'+row.replace('Aria','').upper())
        #             if not os.path.exists(name_bar):
        #                 os.makedirs(name_bar)

        #             name_bar=path.join(name_bar,plot_name)

        #             if len(rows_groups[row][0]) == 0:  # no sub-groups
        #                 data_grouped = data.groupby(row, sort=True)
        #                 if data_grouped:
        #                     bar_plot(name_bar + IMAGE_EXTENSION, data_grouped, third_columns_names_origin,
        #                                 'Intervals' + '\n' + str(row).replace('Aria','').upper() if 'Clef' not in name else 'Clefs' + str(row).replace('Aria','').upper(), title)
        #             else: #subgroups
        #                 for i, subrow in enumerate(rows_groups[row][0]):
        #                     if subrow not in EXCEPTIONS:
        #                         data_grouped = data.groupby(subrow)
        #                         bar_plot(name_bar+'_'+subrow + IMAGE_EXTENSION, data_grouped, third_columns_names_origin,
        #                                 'Intervals' + str(row).replace('Aria','').upper() if 'Clef' not in name else 'Clefs' + str(row).replace('Aria','').upper(), title)

        # else:
        #     name_bar = path.join(
        #         results_path, 'visualisations', name.replace('.xlsx', IMAGE_EXTENSION))
        #     bar_plot(name_bar, data, third_columns_names_origin,'Harmony', title)
    except Exception as e:
        _cfg.write_logger.warn(get_color('WARNING')+'{}  Problem found: {}{}'.format(name, e, RESET_SEQ))



    # num_chordTypes = sort([c.replace('Chord types', '') for c in data.columns if 'Chord types' in c], sorting_lists['ChordTypeGrouppingSorting'])
    # num_additions = [c.replace('Additions', '') for c in data.columns if 'Additions' in c]
    # second_column_names = [('Harmonic rhythm', 3 + len(total_sections)), ('Modulations', len(num_modulations)), ('Numerals', len(num_numerals)), ('Chord types', len(num_chordTypes)), ('Additions', len(num_additions))]
    # third_column_names = ['Average', 'Voice', 'No_voice'] + total_sections + num_modulations + num_numerals + num_chordTypes + num_additions
    # column_names = columns_alike_our_data(third_column_names, second_column_names)
    # second_column_names = [('', 1)] + second_column_names
    # third_column_names = ["Total analysed"] +third_column_names
    # column_names = ["Total analysed"] + column_names
    # computations = ['sum']*len(column_names)

def Chords(rows_groups: dict, not_used_cols: dict, factor, _cfg: Configuration, data: DataFrame, results_path: str,pre_string, name: str, visualiser_lock: Lock, groups: list=None, additional_info: list=[]):
    try:
        workbook = openpyxl.Workbook()
        excel_name=get_excel_name(pre_string, name)
        data_general = data[metadata_columns+ ['Total analysed']].copy()
        data = data[set(data.columns).difference(list(data_general.columns))]
        data_general = data_general.dropna(how='all', axis=1)
        data = data.dropna(how='all', axis=1)
        data.columns=[i.replace(CHORDS_GROUPING_prefix, '') for i in data.columns]
        data.columns=[i.replace(CHORD_prefix, '') for i in data.columns]

        
        #TODO: fix this sorting with johannes's function
        data=sort_columns(data, _cfg.sorting_lists['NumeralsSorting'])

        third_columns_names = data.columns.to_list()

        # second_column_names = [("", 1), ("Chords", len(third_columns_names))]
        third_columns_names.insert(0, 'Total analysed')
        data = pd.concat([data_general, data], axis=1)

        # computations = ["sum"] + ["mean"] * (len(third_columns_names)-1)
        computations = ["sum"]*len(third_columns_names)

        Create_excel(workbook.create_sheet("Total Chords"), third_columns_names, data, third_columns_names, computations, _cfg.sorting_lists,
                     groups=groups, average=True, last_column=True, last_column_average=False, additional_info=additional_info, ponderate=True)
        if factor>=1:
            Create_excel(workbook.create_sheet("Weighted"), third_columns_names, data, third_columns_names, computations, _cfg.sorting_lists,
                        groups=groups, per=False, average=True, last_column=True, last_column_average=False, additional_info=additional_info)

        save_workbook(os.path.join(results_path,excel_name), workbook, NARROW)

        # with visualiser_lock: #Apply when threads are usedwith visualizer_lock=threading.Lock()
        third_columns_names.remove('Total analysed')
        title = 'Chords'

        # VISUALISATIONS
        # if groups:
        #     data_grouped = data.groupby(list(groups))
        #     for g, datag in data_grouped:
        #         result_visualisations = results_path + \
        #             '\\visualisations\\' + str(g.replace('/', '_'))
        #         if not os.path.exists(result_visualisations):
        #             os.mkdir(result_visualisations)
        #         name_bar = result_visualisations + \
        #             '\\' + name.replace('.xlsx', IMAGE_EXTENSION)
        #         bar_plot_extended(name_bar, datag, columns, 'Density',
        #                           'Density', title, second_title=str(g))

        # elif factor == 1:  # 
        #     groups = [i for i in rows_groups]
        #     for row in rows_groups:
        #         plot_name = name.replace(
        #             '.xlsx', '') + '_Per_' + str(row.upper()) + IMAGE_EXTENSION
        #         name_bar = results_path + '\\visualisations\\' + plot_name
        #         if row not in not_used_cols:
        #             if len(rows_groups[row][0]) == 0:  # no sub-groups
        #                 data_grouped = data.groupby(row, sort=True)
        #                 if data_grouped:
        #                     line_plot_extended(
        #                     name_bar, data_grouped, columns, 'Instrument', 'Density', title, second_title='Per ' + str(row))
        #             else:
        #                 for i, subrow in enumerate(rows_groups[row][0]):
        #                     if subrow not in EXCEPTIONS:
        #                         plot_name = name.replace(
        #                             '.xlsx', '') + '_Per_' + str(row.upper()) + '_' + str(subrow) + IMAGE_EXTENSION
        #                         name_bar = results_path + '\\visualisations\\' + plot_name
        #                         data_grouped = data.groupby(subrow)
        #                         line_plot_extended(
        #                             name_bar, data_grouped, columns, 'Instrument', 'Density', title, second_title= 'Per ' + str(subrow))
        # else:
        #     for instr in third_columns_names:
        #         columns=data['AriaName']
        #         name_bar = results_path + '\\visualisations\\' + instr + \
        #             name.replace('.xlsx', IMAGE_EXTENSION)
        #         bar_plot_extended(name_bar, data, columns,
        #                         'Density', 'Density', title + ' ' + instr, instr=instr)
    except Exception as e:
        _cfg.write_logger.warn(get_color('WARNING')+'{}  Problem found: {}{}'.format(name, e, RESET_SEQ))

def Triple_harmonic_excel(rows_groups: dict, not_used_cols: dict, factor, _cfg: Configuration, data: DataFrame, results_path: str, 
                            pre_string, name: str, visualiser_lock: Lock, groups: list=None, additional_info: list=[]):
        
    workbook = openpyxl.Workbook()
    excel_name=get_excel_name(pre_string, name)
    try:
        data, data_general = SeparateDataframes(data)
        if 'functions' in name:
            (data1, data2, data3, third_columns_names,
            third_columns_names2, third_columns_names3,
            second_column_names, second_column_names2,
            second_column_names3) = Process_data(data, NUMERALS_prefix, CHORDS_GROUPING_prefix, CHORDS_GROUPING_prefix,_cfg.sorting_lists['ModulationG1Sorting'],_cfg.sorting_lists['ModulationG2Sorting'],_cfg.sorting_lists['ModulationG2Sorting'])
        
        elif 'Key' in name:
            (data1, data2, data3, third_columns_names, 
            third_columns_names2, third_columns_names3, 
            second_column_names, second_column_names2, 
            second_column_names3) = Process_data(data, KEY_prefix, KEY_GROUPING, KEY_GROUPING,_cfg.sorting_lists['NumeralsSorting'],_cfg.sorting_lists['ModulationG1Sorting'],_cfg.sorting_lists['ModulationG2Sorting'])

        computations = ["sum"] + ['mean'] * (len(third_columns_names))
        computations2 = ['sum'] + ['mean'] * (len(third_columns_names2))
        computations3 = ['sum'] + ['mean'] * (len(third_columns_names3))

        data1 = pd.concat([data_general, data1], axis=1)
        data2 = pd.concat([data_general, data2], axis=1)
        data3 = pd.concat([data_general, data3], axis=1)

        Create_excel(workbook.create_sheet("Weighted"),
         third_columns_names, data1, third_columns_names,
          computations, _cfg.sorting_lists, groups=groups,
            data2=data2,
                last_column=True, last_column_average=False, second_columns=second_column_names,
                columns2=third_columns_names2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, 
                data3=data3,
                columns3=third_columns_names3,  third_columns3=third_columns_names3, computations_columns3=computations3, second_columns3=second_column_names3,
                additional_info=additional_info, ponderate=False)
        
        if factor>=1:
            Create_excel(workbook.create_sheet("Horizontal"),
         third_columns_names, data1, third_columns_names,
          computations, _cfg.sorting_lists, groups=groups,data2=data2,
          last_column=True, last_column_average=False, second_columns=second_column_names,
                    columns2=third_columns_names2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, 
                    data3=data3, columns3=third_columns_names3,  third_columns3=third_columns_names3, computations_columns3=computations3, second_columns3=second_column_names3,
                additional_info=additional_info, ponderate=False)
                
        save_workbook(os.path.join(results_path, excel_name), workbook, NORMAL_WIDTH)
        
        # with visualiser_lock: #Apply when threads are usedwith visualizer_lock=threading.Lock()
        # third_columns_names.remove('Total analysed')

        title = name

        # VISUALISATIONS
        # if groups:
        #     data_grouped = data.groupby(list(groups))
        #     for g, datag in data_grouped:
        #         result_visualisations = results_path + \
        #             '\\visualisations\\' + str(g.replace('/', '_'))
        #         if not os.path.exists(result_visualisations):
        #             os.mkdir(result_visualisations)
        #         name_bar = result_visualisations + \
        #             '\\' + name.replace('.xlsx', IMAGE_EXTENSION)
        #         bar_plot_extended(name_bar, datag, columns, 'Density',
        #                           'Density', title, second_title=str(g))

        # elif factor == 1:  # 
        #     groups = [i for i in rows_groups]
        #     for row in rows_groups:
        #         plot_name = name.replace(
        #             '.xlsx', '') + '_Per_' + str(row.upper()) + IMAGE_EXTENSION
        #         name_bar = results_path + '\\visualisations\\' + plot_name
        #         if row not in not_used_cols:
        #             if len(rows_groups[row][0]) == 0:  # no sub-groups
        #                 data_grouped = data.groupby(row, sort=True)
        #                 if data_grouped:
        #                     line_plot_extended(
        #                     name_bar, data_grouped, columns, 'Instrument', 'Density', title, second_title='Per ' + str(row))
        #             else:
        #                 for i, subrow in enumerate(rows_groups[row][0]):
        #                     if subrow not in EXCEPTIONS:
        #                         plot_name = name.replace(
        #                             '.xlsx', '') + '_Per_' + str(row.upper()) + '_' + str(subrow) + IMAGE_EXTENSION
        #                         name_bar = results_path + '\\visualisations\\' + plot_name
        #                         data_grouped = data.groupby(subrow)
        #                         line_plot_extended(
        #                             name_bar, data_grouped, columns, 'Instrument', 'Density', title, second_title= 'Per ' + str(subrow))
        # else:
        #     for instr in third_columns_names:
        #         columns=data['AriaName']
        #         name_bar = results_path + '\\visualisations\\' + instr + \
        #             name.replace('.xlsx', IMAGE_EXTENSION)
        #         bar_plot_extended(name_bar, data, columns,
        #                         'Density', 'Density', title + ' ' + instr, instr=instr)
    except Exception as e:
        _cfg.write_logger.warn(get_color('WARNING')+'{}  Problem found: {}{}'.format(name, e, RESET_SEQ))

def SeparateDataframes(data):
    data_general = data[metadata_columns+ ['Total analysed']].copy()
    data = data[set(data.columns).difference(list(data_general.columns))]
    data = data.dropna(how='all', axis=1)
    data_general = data_general.dropna(how='all', axis=1)
    return data,data_general

def Process_data(data, prefix1, prefix2, prefix3, sorting_list1, sorting_list2, sorting_list3):
    data1 = data[[i for i in data.columns if prefix1 in i]]
    data1.columns = [i.replace(prefix1,'') for i in data1.columns]
    pass   
    data2 = data[[i for i in data.columns if prefix2 + '1' in i]]
    data2.columns = [i.replace(prefix2 + '1','') for i in data2.columns]

    data3 = data[[i for i in data.columns if prefix2 + '2' in i]]
    data3.columns = [i.replace(prefix3 + '2', 'Grouped_') for i in data3.columns]

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
    second_column_names3 = name_second_columns(third_columns_names3, prefix3+ '_2')

    return data1,data2,data3,third_columns_names,third_columns_names2,third_columns_names3,second_column_names,second_column_names2,second_column_names3

def name_second_columns(third_columns_names, name):
    second_column_names = [("", 1), (name, len(third_columns_names))]
    return second_column_names

def insert_total_analysed(columns_names):
    columns_names.insert(0, 'Total analysed')


# def Keyareas_columns(rows_groups: dict, not_used_cols: dict, keyareas, sorting_lists, mandatory_word = None, complementary_info = None, computations = 'sum', forbiden_word = ''):
#     if mandatory_word != None and complementary_info != None:
#         keyword = mandatory_word+complementary_info
#     elif mandatory_word != None:
#         keyword = mandatory_word
#     else:
#         keyword = ''
#     all_columns = keyareas.columns.tolist()
#     #general_cols = ['Id', 'RealScoring']
#     general_cols = copy.deepcopy(not_used_cols)
#     # for row in rows_groups:
#     #     if len(rows_groups[row][0]) == 0:
#     #         general_cols.append(row)
#     #     else:
#     #         general_cols += rows_groups[row][0]
#     first_group_columns = {'data': keyareas,
#                             'first_columns': None,
#                             'second_columns': None,
#                             'third_columns': None,
#                             'computations_columns': None,
#                             'columns': None}
#     third_columns_names = list(set(all_columns) - set(general_cols))
#     # we pre-estimate the columns to use (based on the need of showing section data or not)
#     if keyword != '':
#         if forbiden_word != '':
#             third_columns_names = [c.replace(keyword, '') for c in third_columns_names if keyword in c and forbiden_word not in c]
#         else:
#             third_columns_names = [c.replace(keyword, '') for c in third_columns_names if keyword in c]
#     else:
#         third_columns_names = [c for c in third_columns_names if 'Section' not in c and 'Compasses' not in c and 'Areas' not in c and 'Modulatory' not in c and 'ModComp' not in c] #all the possibilities without keywords

#     # We pick only the columns that represent 'Key'
#     cleaned_third_columns_names = [tcn.replace('Key', '') for tcn in third_columns_names if 'Key' in tcn and 'Groupping' not in tcn]

#     third_columns_names = sort(cleaned_third_columns_names, sorting_lists['Modulation'])
#     computations_list = [computations]*len(cleaned_third_columns_names) # This sheet is about adding, so only sum is computed
#     first_group_columns['second_column_names'] = [('', 1), ('Key', len(cleaned_third_columns_names))]
#     if keyword != '':
#         column_names =  columns_alike_our_data(third_columns_names, [(keyword, len(third_columns_names))], [('Key', len(third_columns_names))])
#     else:
#         column_names =  columns_alike_our_data(third_columns_names, [('Key', len(third_columns_names))])
#     first_group_columns['third_columns_names'] = ['Total analysed'] + third_columns_names
#     first_group_columns['column_names'] = ['Total analysed'] + column_names
#     first_group_columns['computations_columns'] = ['sum'] + computations_list
    
#     # Creamos los datos para las segundas agrupaciones
#     third_columns_names = list(set(all_columns) - set(general_cols))
#     if keyword != '':
#         if forbiden_word != '':
#             third_columns_names = [c.replace(keyword, '') for c in third_columns_names if keyword in c and forbiden_word not in c]
#         else:
#             third_columns_names = [c.replace(keyword, '') for c in third_columns_names if keyword in c]
#     else:
#         third_columns_names = [c for c in third_columns_names if 'Section' not in c and 'Compasses' not in c and 'Areas' not in c and 'Modulatory' not in c and 'ModComp' not in c]

#     second_group_columns = {'data': None,
#                             'first_columns': None,
#                             'second_columns': None,
#                             'third_columns': None,
#                             'computations_columns': None,
#                             'columns': None}
#     cleaned_third_columns_names = [tcn.replace('KeyGroupping1', '') for tcn in third_columns_names if 'KeyGroupping1' in tcn]
#     second_group_columns['third_columns'] = sort(cleaned_third_columns_names, sorting_lists['ModulationG1Sorting'])
#     second_group_columns['second_columns'] = [('', 1), ('KeyGroupping1', len(cleaned_third_columns_names))]
#     second_group_columns['computations_columns'] = [computations]*len(cleaned_third_columns_names) # esta hoja va de sumar, así que en todas las columnas el cómputo que hay que hacer es sumar!
#     if keyword != '':
#         second_group_columns['columns'] = columns_alike_our_data(second_group_columns['third_columns'], [(keyword, len(cleaned_third_columns_names))], [('KeyGroupping1', len(cleaned_third_columns_names))])
#     else:
#         second_group_columns['columns'] = columns_alike_our_data(second_group_columns['third_columns'], [('KeyGroupping1', len(cleaned_third_columns_names))])

#     second_group_columns['data'] = keyareas
#     second_group_columns['third_columns'] = ['Total analysed'] + second_group_columns['third_columns']
#     second_group_columns['computations_columns'] = ['sum'] + second_group_columns['computations_columns']
#     second_group_columns['columns'] = ['Total analysed'] + second_group_columns['columns']
    
#     # creamos los datos para las terceras agrupaciones
#     third_columns_names = list(set(all_columns) - set(general_cols))
#     if keyword != '':
#         if forbiden_word != '':
#             third_columns_names = [c.replace(keyword, '') for c in third_columns_names if keyword in c and forbiden_word not in c]
#         else:
#             third_columns_names = [c.replace(keyword, '') for c in third_columns_names if keyword in c]
#     else:
#         third_columns_names = [c for c in third_columns_names if 'Section' not in c and 'Compasses' not in c and 'Areas' not in c and 'Modulatory' not in c and 'ModComp' not in c]

#     third_group_columns = {'data': None,
#                             'first_columns': None,
#                             'second_columns': None,
#                             'third_columns': None,
#                             'computations_columns': None,
#                             'columns': None}
#     cleaned_third_columns_names = [tcn.replace('KeyGroupping2', '') for tcn in third_columns_names if 'KeyGroupping2' in tcn]
#     third_group_columns['third_columns'] = sort(cleaned_third_columns_names, sorting_lists['ModulationG2Sorting'])
#     third_group_columns['second_columns'] = [('', 1), ('KeyGroupping2', len(cleaned_third_columns_names))]
#     third_group_columns['computations_columns'] = [computations]*len(cleaned_third_columns_names) # esta hoja va de sumar, así que en todas las columnas el cómputo que hay que hacer es sumar!
#     if keyword != '':
#         third_group_columns['columns'] = columns_alike_our_data(third_group_columns['third_columns'], [(keyword, len(cleaned_third_columns_names))], [('KeyGroupping2', len(cleaned_third_columns_names))])
#     else:
#         third_group_columns['columns'] = columns_alike_our_data(third_group_columns['third_columns'], [('KeyGroupping2', len(cleaned_third_columns_names))])
#     third_group_columns['data'] = keyareas
#     third_group_columns['third_columns'] = ['Total analysed'] + third_group_columns['third_columns']
#     third_group_columns['computations_columns'] = ['sum'] + third_group_columns['computations_columns']
#     third_group_columns['columns'] = ['Total analysed'] + third_group_columns['columns']

#     return first_group_columns, second_group_columns, third_group_columns

# ########################################################################
# # Function in charge of generating Ia.keyareas
# ########################################################################
# def Keyareas(rows_groups: dict, not_used_cols: dict, results_path, keyareas, combinations = False, groups = None):
#     # additional_info = {"Label":["Aria"], "Aria":['Label']}
#     workbook = openpyxl.Workbook()
#     first_group_columns,second_group_columns,third_group_columns = Keyareas_columns(keyareas)
#     first_group_columns_A,second_group_columns_A,third_group_columns_A = Keyareas_columns(keyareas, mandatory_word = 'Section', complementary_info = 'A', forbiden_word='ModComp')
#     first_group_columns_B,second_group_columns_B,third_group_columns_B = Keyareas_columns(keyareas, mandatory_word = 'Section', complementary_info = 'B', forbiden_word='ModComp')
    
#     print('\t\t Horizontal per')
#     excel_sheet(workbook.create_sheet("Horizontal Per"), first_group_columns['column_names'], keyareas, first_group_columns['third_columns_names'], first_group_columns['computations_columns'], 
#                 second_columns=first_group_columns['second_column_names'], per = True, average=True, last_column=True, last_column_average = False, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns, 
#                 third_subgroup=True, third_subgroup_info=third_group_columns,
#                 groups = groups)
#     print('\t\t Vertical per')
#     excel_sheet(workbook.create_sheet("Vertical Per"), first_group_columns['column_names'], keyareas, first_group_columns['third_columns_names'], first_group_columns['computations_columns'], 
#                 second_columns=first_group_columns['second_column_names'], per = True, average = False, last_column=True, last_column_average = True, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns,
#                 third_subgroup=True, third_subgroup_info=third_group_columns,
#                 groups = groups)
#     print('\t\t Horizontal per A')
#     excel_sheet(workbook.create_sheet("Horizontal Per A"), first_group_columns_A['column_names'], keyareas, first_group_columns_A['third_columns_names'], first_group_columns_A['computations_columns'], 
#                 second_columns=first_group_columns_A['second_column_names'], per = True, average=True, last_column=True, last_column_average = False, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns_A, 
#                 third_subgroup=True, third_subgroup_info=third_group_columns_A,
#                 groups = groups)
#     print('\t\t Vertical per A')
#     excel_sheet(workbook.create_sheet("Vertical Per A"), first_group_columns_A['column_names'], keyareas, first_group_columns_A['third_columns_names'], first_group_columns_A['computations_columns'], 
#                 second_columns=first_group_columns_A['second_column_names'], per = True, average = False, last_column=True, last_column_average = True, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns_A,
#                 third_subgroup=True, third_subgroup_info=third_group_columns_A,
#                 groups = groups)
#     print('\t\t Horizontal per B')
#     excel_sheet(workbook.create_sheet("Horizontal Per B"), first_group_columns_B['column_names'], keyareas, first_group_columns_B['third_columns_names'], first_group_columns_B['computations_columns'], 
#                 second_columns=first_group_columns_B['second_column_names'], per = True, average=True, last_column=True, last_column_average = False, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns_B, 
#                 third_subgroup=True, third_subgroup_info=third_group_columns_B,
#                 groups = groups)
#     print('\t\t Horizontal per B')
#     excel_sheet(workbook.create_sheet("Vertical Per B"), first_group_columns_B['column_names'], keyareas, first_group_columns_B['third_columns_names'], first_group_columns_B['computations_columns'], 
#                 second_columns=first_group_columns_B['second_column_names'], per = True, average = False, last_column=True, last_column_average = True, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns_B,
#                 third_subgroup=True, third_subgroup_info=third_group_columns_B,
#                 groups = groups)
#     #borramos la hoja por defecto
#     if "Sheet" in workbook.get_sheet_names():
#         std=workbook.get_sheet_by_name('Sheet')
#         workbook.remove_sheet(std)
#     workbook.save(os.path.join(results_path, "Ia.Keyareas.xlsx"))
# ########################################################################
# # Function in charge of generating Ib.Keyareas_weighted
# ########################################################################

# # def Keyareas_weighted(results_path, keyareas, combinations = False, groups = None):
# def Keyareas_weighted(rows_groups: dict, not_used_cols: dict, factor, _cfg: Configuration, data: DataFrame, results_path: str, name: str, sorting_lists: list, visualiser_lock: Lock, groups: list=None, additional_info: list=[]):

#     # additional_info = {"Label":["Aria"], "Aria":['Label']}
#     workbook = openpyxl.Workbook()
#     ############
#     # COMPASES #
#     ############
#     first_group_columns,second_group_columns,third_group_columns = Keyareas_columns(data,sorting_lists, 'Compasses', computations = 'mean')
    
#     excel_sheet(workbook.create_sheet("WH_proportions"), first_group_columns['column_names'], data, first_group_columns['third_columns_names'], first_group_columns['computations_columns'], 
#                 second_columns=first_group_columns['second_column_names'], per = True, average=True, last_column=True, last_column_average = False, additional_info=additional_info,
                
                
#                 second_subgroup=True, second_subgroup_info=second_group_columns, 
#                 third_subgroup=True, third_subgroup_info=third_group_columns,
#                 groups = groups)
                
#     excel_sheet(workbook.create_sheet("WV_proportions"), first_group_columns['column_names'], data, first_group_columns['third_columns_names'], first_group_columns['computations_columns'], 
#                 second_columns=first_group_columns['second_column_names'], per = True, average = False, last_column=True, last_column_average = True, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns,
#                 third_subgroup=True, third_subgroup_info=third_group_columns,
#                 groups = groups)
#     ############
#     # AREAS    #
#     ############
#     first_group_columns,second_group_columns,third_group_columns = Keyareas_columns(data, sorting_lists, 'Modulatory', computations = 'mean')
#     excel_sheet(workbook.create_sheet("WH_key_areas"), first_group_columns['column_names'], data, first_group_columns['third_columns_names'], first_group_columns['computations_columns'], 
#                 second_columns=first_group_columns['second_column_names'], per = True, average=True, last_column=True, last_column_average = False, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns, 
#                 third_subgroup=True, third_subgroup_info=third_group_columns,
#                 groups = groups) #This is the main case in which the weighted FLAG is turned on
#     #################
#     # ALLWEIGHTED   #
#     #################
#     first_group_columns,second_group_columns,third_group_columns = Keyareas_columns(data, sorting_lists, 'ModComp', computations = 'mean', forbiden_word='Section')
#     excel_sheet(workbook.create_sheet("WH_allweighted"), first_group_columns['column_names'], data, first_group_columns['third_columns_names'], first_group_columns['computations_columns'], 
#                 second_columns=first_group_columns['second_column_names'], per = True, average=True, last_column=True, last_column_average = False, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns, 
#                 third_subgroup=True, third_subgroup_info=third_group_columns,
#                 groups = groups) #This is the main case in which the weighted FLAG is turned on
#     excel_sheet(workbook.create_sheet("WV_allweighted"), first_group_columns['column_names'], data, first_group_columns['third_columns_names'], first_group_columns['computations_columns'], 
#                 second_columns=first_group_columns['second_column_names'], per = True, average=False, last_column=True, last_column_average = True, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns, 
#                 third_subgroup=True, third_subgroup_info=third_group_columns,
#                 groups = groups) #This is the main case in which the weighted FLAG is turned on
    
#     first_group_columns_A,second_group_columns_A,third_group_columns_A = Keyareas_columns(data, sorting_lists, mandatory_word = 'ModCompSection', complementary_info = 'A')
#     first_group_columns_B,second_group_columns_B,third_group_columns_B = Keyareas_columns(data, sorting_lists, mandatory_word = 'ModCompSection', complementary_info = 'B')
#     #################
#     # SECTION A   #
#     #################
#     excel_sheet(workbook.create_sheet("WH_allweighted_A"), first_group_columns_A['column_names'], data, first_group_columns_A['third_columns_names'], first_group_columns_A['computations_columns'], 
#                 second_columns=first_group_columns_A['second_column_names'], per = True, average=True, last_column=True, last_column_average = False, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns_A, 
#                 third_subgroup=True, third_subgroup_info=third_group_columns_A,
#                 groups = groups) #This is the main case in which the weighted FLAG is turned on
#     excel_sheet(workbook.create_sheet("WV_allweighted_A"), first_group_columns_A['column_names'], data, first_group_columns_A['third_columns_names'], first_group_columns_A['computations_columns'], 
#                 second_columns=first_group_columns_A['second_column_names'], per = True, average=False, last_column=True, last_column_average = True, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns_A, 
#                 third_subgroup=True, third_subgroup_info=second_group_columns_A,
#                 groups = groups) #This is the main case in which the weighted FLAG is turned on
#     #################
#     # SECTION B   #
#     #################
#     excel_sheet(workbook.create_sheet("WH_allweighted_B"), first_group_columns_B['column_names'], data, first_group_columns_B['third_columns_names'], first_group_columns_B['computations_columns'], 
#                 second_columns=first_group_columns_B['second_column_names'], per = True, average=True, last_column=True, last_column_average = False, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns_B, 
#                 third_subgroup=True, third_subgroup_info=third_group_columns_B,
#                 groups = groups) #This is the main case in which the weighted FLAG is turned on
#     excel_sheet(workbook.create_sheet("WV_allweighted_B"), first_group_columns_B['column_names'], data, first_group_columns_B['third_columns_names'], first_group_columns_B['computations_columns'], 
#                 second_columns=first_group_columns_B['second_column_names'], per = True, average=False, last_column=True, last_column_average = True, additional_info=additional_info,
#                 second_subgroup=True, second_subgroup_info=second_group_columns_B, 
#                 third_subgroup=True, third_subgroup_info=third_group_columns_B,
#                 groups = groups) #This is the main case in which the weighted FLAG is turned on

#     if "Sheet" in workbook.get_sheet_names():
#         std=workbook.get_sheet_by_name('Sheet')
#         workbook.remove_sheet(std)
#     workbook.save(os.path.join(results_path, "Ib.Keyareas_weighted.xlsx"))
# def get_sorting_lists():
#     # RoleSorting = general_sorting.get_role_sorting() # Only valid for DIDON
#     #harmony
#     modulations = harmony_sorting.get_modulations_sorting()
#     modulationsG1 = harmony_sorting.get_modulationsGrouping1_sorting()
#     modulationsG2 = harmony_sorting.get_modulationsGrouping2_sorting()
#     chordTypes, chordTypesG = harmony_sorting.get_chordtype_sorting()
#     return {"RoleSorting": [i.lower() for i in RoleSorting],
#             "FormSorting": [i.lower() for i in FormSorting],
#             "KeySorting": KeySorting,
#             "KeySignatureSorting": KeySignatureSorting,
#             "KeySignatureGroupedSorted": KeySignatureGroupedSorted,
#             "TimeSignatureSorting": TimeSignatureSorting,
#             "TempoSorting": TempoSorting + [''], #a veces algunas puede ser nan, ya que no tienen tempo mark, las nan las ponemos al final
#             "TempoGroupedSorting1": TempoGroupedSorting1 + [''],
#             "TempoGroupedSorting2": TempoGroupedSorting2 + [''],
#             "Intervals": Intervals,
#             "Intervals_absolute": Intervals_absolute,
#             "Clefs": clefs,
#             "ScoringSorting": scoring_sorting,
#             "ScoringFamilySorting": scoring_family,
#             "ScaleDegrees": scale_degrees,
#             "ModulationG1Sorting": modulationsG1,
#             "ModulationG2Sorting": modulationsG2,
#             "Modulation": modulations,
#             "ChordTypeGrouppingSorting": chordTypesG,
#             }
