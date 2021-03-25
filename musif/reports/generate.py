########################################################################
# WRITE MODULE
########################################################################
# This script is ment to read the intermediate files computed by the 
# read module and perform several computations while grouping the data
# based on several characteristics. 
# Writes the final report files as well as generates the visualisations
########################################################################
import concurrent
import copy
import json
import logging
import math
import os
import sys
import threading  # for the lock used for visualising, as matplotlib is not thread safe
from itertools import permutations
from os import path

import numpy as np
import openpyxl
import pandas as pd
from music21 import interval, note, pitch
from source.SortingGroupings import general_sorting, melody_sorting
from source.visualisations import *
from tqdm import tqdm

if not os.path.exists(path.join(os.getcwd(), 'source', 'logs')):
    os.mkdir(path.join(os.getcwd(), 'source', 'logs'))
fh = logging.FileHandler(path.join(os.getcwd(), 'source', 'logs', 'write.log'), 'w+')
fh.setLevel(logging.ERROR)
logger = logging.getLogger("write")
logger.addHandler(fh)

# Groupings present in every file generated
# The structure shows the grouping name as key, and as value a tuple containing its subgroupings and the sorting methods
rows_groups = {"Opera":([], "Alphabetic"),
                "Label": ([], "Alphabetic"),
                "Aria": ([], "Alphabetic"), 
                "Composer": ([], "Alphabetic"), 
                "Date": ([
                    "Year",
                    "Decade"
                ], ["Alphabetic", "Alphabetic"]), 
                "Geography": ([
                    "City",
                    "Country"
                ], ["Alphabetic", "Alphabetic"]),
                "Drama": ([
                    "Act",
                    "Scene",
                    "Act&Scene"
                ], ["Alphabetic", "Alphabetic", "Alphabetic"]),
                "Character": ([
                    "Role",
                    "RoleType",
                    "Gender"
                ], ["RoleSorting", "Alphabetic", "Alphabetic"]),
                "Form":([], "FormSorting"),
                "Clef":([], "Alphabetic"),
                "Key": ([
                    "Key",
                    "Mode",
                    "KeySignature",
                    "KeySignatureGrouped"], ["KeySorting", "Alphabetic", "Alphabetic", "KeySignatureSorting", "KeySignatureGroupedSorted"]),
                "Metre":([
                    "TimeSignature",
                    "TimeSignatureGrouped"
                ], ["TimeSignatureSorting", "Alphabetic"]),
                "Tempo":([
                    "Tempo",
                    "TempoGrouped1",
                    "TempoGrouped2"
                ], ["TempoSorting", "TempoGroupedSorting1", "TempoGroupedSorting2"]),
                "Scoring":([
                    "AbrScoring",
                    "RealScoringGrouped"
                ], ["ScoringSorting", "ScoringFamilySorting"]) 
            }
not_used_cols = ['Id', 'RealScoring', 'Total analysed', 'OldClef']

sorting_lists = {} # Changes in get_sorting_lists()

# Some combinations are not needed when using more than one factor
forbiden_groups = {"Opera":['Opera'],
                    "Label": ['Opera', 'Label'],
                    "Aria": ['Aria', 'Opera'],
                    "Composer": ['Composer'],
                    "Year":['Year', 'Decade'],
                    "Decade":['Decade'],
                    "City":['City', 'Country'],
                    "Country":['Country'],
                    "Act":["Act", 'Act&Scene'],
                    "Scene":["Scene", "Act&Scene"],
                    "Act&Scene":["Act", 'Scene', 'Act&Scene'],
                    'Role':["Role", "RoleType", "Gender"],
                    'RoleType':["RoleType", "Gender"],
                    'Gender':["Gender"],
                    'Form':['Form'],
                    "Clef":['Clef'],
                    'Key':['Form', 'Mode', 'Final', 'KeySignature', 'KeySignatureGrouped'],
                    'Mode':['Mode', 'Final'],
                    'Final':['Final', 'Key', 'KeySignature'],
                    'KeySignature':['Key', 'Final', 'KeySignature', 'KeySignatureGrouped'],
                    'KeySignatureGrouped':['KeySignatureGrouped'],
                    'TimeSignature':['TimeSignature', 'TimeSignatureGrouped'],
                    "TimeSignatureGrouped": ['TimeSignatureGrouped'],
                    'Tempo':['Tempo',"TempoGrouped1","TempoGrouped2"],
                    'TempoGrouped1':['TempoGrouped1',"TempoGrouped2"],
                    'TempoGrouped2':['TempoGrouped2'],
                    "AbrScoring":["AbrScoring", "RealScoringGrouped"],
                    "RealScoringGrouped":["RealScoringGrouped"]
                    }

yellowFill = openpyxl.styles.PatternFill(start_color='F9E220', end_color='F9E220',fill_type='solid')
greenFill = openpyxl.styles.PatternFill(start_color='98E891', end_color='98E891',fill_type='solid')
orangeFill = openpyxl.styles.PatternFill(start_color='EE6513', end_color='EE6513',fill_type='solid')
titles1Fill = openpyxl.styles.PatternFill(start_color='F97626', end_color='F97626',fill_type='solid')
titles2Fill = openpyxl.styles.PatternFill(start_color='FA9455', end_color='FA9455',fill_type='solid')
titles3Fill = openpyxl.styles.PatternFill(start_color='FBBA93', end_color='FBBA93',fill_type='solid')
factors_Fill = [openpyxl.styles.PatternFill(start_color='06CAFF', end_color='06CAFF',fill_type='solid'),
                openpyxl.styles.PatternFill(start_color='18ADD5', end_color='18ADD5',fill_type='solid'),
                openpyxl.styles.PatternFill(start_color='1B94B4', end_color='1B94B4',fill_type='solid'),
                openpyxl.styles.PatternFill(start_color='11718A', end_color='11718A',fill_type='solid')]

bold = openpyxl.styles.Font(bold=True)
center = openpyxl.styles.Alignment(horizontal='center')

########################################################
# This function prints the names in the excell in bold
########################################################
def write_columns_titles(hoja, row, column, column_names):
    for c in column_names:
        hoja.cell(row, column).value = c
        hoja.cell(row, column).font = bold
        hoja.cell(row, column).fill = titles3Fill
        column += 1

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
        hoja.merge_cells(start_row=row, start_column=column, end_row=row, end_column=column + c[1] - 1)
        column += c[1]

def print_averages_total(hoja, row, values, lable_column, values_column, average=False, per=False, exception=None):
    hoja.cell(row, lable_column).value = "Average" if average else "Total"
    hoja.cell(row, lable_column).fill = orangeFill

    for i, v in enumerate(values):
        if exception and i == exception: #unicamente ocurre en % Trimmed en iValues
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

###############################################################################################
# Function used to carry out every kind of computation needed, as determined by 'computation'
###############################################################################################
def compute_value(column_data, computation, ponderate_data, not_grouped_information, ponderate):
    value = 0
    if computation == "mean":
        if not ponderate:
            value = round(sum(column_data) / len(column_data), 3)
        else:
            s = 0
            for v, w in zip(column_data, ponderate_data):
                s += v * w
            value = round(s / sum(ponderate_data), 3)

    elif computation == "min":
        value = min(column_data)
    elif computation == "max":
        value = max(column_data)
    elif computation == "minNote":
        pitch_ps = [pitch.Pitch(n).ps for n in column_data]
        min_ps = min(pitch_ps)
        value = column_data.tolist()[pitch_ps.index(min_ps)]
    elif computation == "maxNote":
        pitch_ps = [pitch.Pitch(n).ps for n in column_data]
        max_ps = max(pitch_ps)
        value = column_data.tolist()[pitch_ps.index(max_ps)]
    elif computation == "meanNote":
        pitch_ps = [pitch.Pitch(n).ps for n in column_data]
        value = note_mean(pitch_ps)
    elif computation == "minInterval":
        interval_semitones = [interval.Interval(n).semitones for n in column_data]
        min_sem = min(interval_semitones)
        value = column_data.tolist()[interval_semitones.index(min_sem)]
    elif computation == "maxInterval":
        interval_semitones = [interval.Interval(n).semitones for n in column_data]
        max_sem = max(interval_semitones)
        value = column_data.tolist()[interval_semitones.index(max_sem)]
    elif computation == "meanInterval" or computation == "meanSemitones":
        lowest_notes_names = [a.split(',')[0] for a in column_data]
        max_notes_names = [a.split(',')[1] for a in column_data]
        min_notes_pitch = [pitch.Pitch(a).ps for a in lowest_notes_names]
        max_notes_pitch = [pitch.Pitch(a).ps for a in max_notes_names]
        mean_min = note_mean(min_notes_pitch, round_mean = True)
        mean_max = note_mean(max_notes_pitch, round_mean = True)
        i = interval.Interval(noteStart = note.Note(mean_min), noteEnd = note.Note(mean_max))
        if computation == "meanInterval":
            value = i.name
        else:
            value = i.semitones
    elif computation == "absoluteInterval" or computation == "absolute":
        lowest_notes_names = [a.split(',')[0] for a in column_data]
        max_notes_names = [a.split(',')[1] for a in column_data]
        min_notes_pitch = [pitch.Pitch(a).ps for a in lowest_notes_names]
        max_notes_pitch = [pitch.Pitch(a).ps for a in max_notes_names]
        minimisimo = min(min_notes_pitch)
        maximisimo = max(max_notes_pitch)
        noteStart = note.Note(lowest_notes_names[min_notes_pitch.index(minimisimo)])
        noteEnd = note.Note(max_notes_names[max_notes_pitch.index(maximisimo)])
        i = interval.Interval(noteStart = noteStart, noteEnd = noteEnd)
        if computation == "absoluteInterval":
            value = i.name
        else:
            value = i.semitones
    elif computation == "sum":
        value = np.nansum(column_data)
        if ponderate and value != 0 and column_data.name != "Total analysed": #PONDERATE WITHT THE TOTAL ANALYSED IN THAT ROW
            values = [] 
            for i in range(len(column_data.tolist())): # not_grouped_information needed for adding all the elements in total
                all_columns = not_grouped_information.columns.tolist()
                total_intervals=np.nansum([not_grouped_information.iloc[i,c] for c in range(len(all_columns)) if 'All' not in all_columns[c]])
                intervals = column_data.tolist()[i]
                values.append((intervals* ponderate_data[i]) / total_intervals)

            value = np.nansum(values) / sum(ponderate_data)
            value = round(value * 100, 3)
    return value

def note_mean(pitch_ps, round_mean = False):
    mean_pitch = sum(pitch_ps) / len(pitch_ps) 
    mean_pitch = mean_pitch if not round_mean else round(mean_pitch)
    if type(mean_pitch) == int or mean_pitch.is_integer():
        p = pitch.Pitch()
        p.ps = mean_pitch
        value = p.nameWithOctave.replace('-', 'b')
    else:
        pitch_up = pitch.Pitch()
        pitch_down = pitch.Pitch()
        pitch_up.ps = math.ceil(mean_pitch)
        pitch_down.ps = math.floor(mean_pitch)
        value = "-".join([pitch_up.nameWithOctave.replace('-', 'b'), pitch_down.nameWithOctave.replace('-', 'b')])
    return value

def interval_mean(interval_semitones):
    mean_semitones = sum(interval_semitones) / len(interval_semitones)
    if mean_semitones.is_integer():
        i = interval.convertSemitoneToSpecifierGeneric(mean_semitones)
        value = str(i[0]) + str(i[1])
    else:
        i_up = math.ceil(mean_semitones)
        i_down = math.floor(mean_semitones)
        nup = interval.convertSemitoneToSpecifierGeneric(i_up)
        ndown = interval.convertSemitoneToSpecifierGeneric(i_down)
        value = "-".join([str(nup[0]) + str(nup[1]), str(ndown[0]) + str(ndown[1])])
    return value

#####################################################################################
# Function to compute the average in every kind of variable, based on a computation #
#####################################################################################
def compute_average(dic_data, computation):
    value = 0
    if computation in ["mean", "min", "sum", "max", "absolute","meanSemitones"]:
        value = round(sum(dic_data) / len(dic_data), 3)
    elif computation in ["minNote", "maxNote"]:
        pitch_ps = [pitch.Pitch(n).ps for n in dic_data]
        value = note_mean(pitch_ps)
    elif computation in ["meanNote"]:
        mean_dic_data = []
        for data in dic_data:
            pitches = [pitch.Pitch(n).ps for n in data.split('-')]
            mean_dic_data.append(sum(pitches) / len(pitches))
        value = note_mean(mean_dic_data)
    elif computation in ["minInterval", "maxInterval", "absoluteInterval"]:
        interval_semitones = [interval.Interval(n).semitones for n in dic_data]
        value = interval_mean(interval_semitones)
    elif computation == "meanInterval":
        mean_dic_data = []
        for data in dic_data:
            semitones = [interval.Interval(n).semitones for n in data.split('-')]
            mean_dic_data.append(sum(semitones) / len(semitones))
        value = interval_mean(mean_dic_data)

    return value

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
                first_columns = None, second_columns = None, per = False, average = False, last_column = False, 
                last_column_average = False, additional_info = None, ponderate = False, not_grouped_df = None):
    len_add_info = 0 #Space for the possible column of additional information
    if additional_info:
        len_add_info = additional_info
    #### WRITE THE COLUMN NAMES (<first>, <second> and third)
    if first_columns:
        write_columns_titles_variable_length(hoja, row_number, column_number + 1 + len_add_info, first_columns, titles1Fill)
        row_number += 1
    if second_columns:
        write_columns_titles_variable_length(hoja, row_number, column_number + 1 + len_add_info, second_columns, titles2Fill)
        row_number += 1
    starting_row = row_number
    write_columns_titles(hoja, row_number, column_number + 1 + len_add_info, third_columns)
    row_number += 1
    exception = -1
    total_analysed_column = "Total analysed" in columns
    cnumber = column_number
    #### PRINT EACH ROW
    valores_columnas = {c:[] for c in columns} #store each result in case of need of calculating the percentage (per = True)
    for s, subgroup in enumerate(grouped): # Subgroup: ex: Berlin when groupping by City
        
        cnumber = column_number# if not total_analysed_column else column_number + 1
        # Print row name
        if type(subgroup[0]) != tuple: #It has no additional information
            hoja.cell(row_number, column_number).value = subgroup[0] # could be a tuple if we have grouped by more than one element
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
                not_grouped_information = not_grouped_df[1][cond].drop(not_grouped_df[0] + ['Total analysed'], axis = 1)
            else:
                for sb in range(len(subgroup[0])):
                    cond = not_grouped_df[1][not_grouped_df[0][sb]] == subgroup[0][sb]
                    not_grouped_information = not_grouped_df[1][cond]
                not_grouped_information = not_grouped_information.drop(not_grouped_df[0] + ['Total analysed'], axis = 1)
        else:
            not_grouped_information = None

        ### COMPUTE EACH COLUMN'S VALUE FOR THE PRESENT ROW (SUBGROUP) AND PRINT IT    
        for i, c in enumerate(columns):
            column_computation = computations_columns[i]
            value = compute_value(subgroup_data[c], column_computation, total_analysed_row, not_grouped_information, ponderate) #absolute value
            if c == "Total analysed":
                total_analysed_row = subgroup_data[c].tolist()
                hoja.cell(row_number, cnumber).value = value
            
            if c == "% Trimmed": #EXCEPTION
                hoja.cell(row_number, cnumber).value = str(round(value * 100, 1)) + '%'
                cnumber += 1
                exception = i - 1
            elif not per:
                hoja.cell(row_number, cnumber).value = str(value) + '%' if ponderate and column_computation == "sum" and c != "Total analysed" else str(value).replace(',', '.')
                cnumber += 1
            
            valores_columnas[c].append(value) # store each value in case of needing to print the percentage   
        row_number += 1
        
    if total_analysed_column: #We don't need Total analysed up to this point
        del valores_columnas['Total analysed']
        computations_columns = computations_columns[1:]
    
    last_used_row = row_number
    if per or last_column: #This are the two conditions in which we need to transpose valores_columnas
        # Transpose valores_columnas to valores_filas (change perspective from column to rows)
        listas_columnas = list(valores_columnas.values())
        keys_columnas = list(valores_columnas.keys())
        valores_filas = []
        len_lists = len(listas_columnas[0])
        for i in range(len_lists):
            valores_filas.append(round(sum([lc[i] for x, lc in enumerate(listas_columnas) if "All" not in keys_columnas[x]]), 3))
        
    ### PRINT EACH CELL IF PER IS TRUE, now that we have all the information
    if per:
        cn = column_number + len_add_info + 2 if total_analysed_column else column_number + len_add_info + 1
        for i in range(len(listas_columnas)): #Traverse each column's information
            row_number = starting_row
            sum_column = sum(listas_columnas[i]) if sum(listas_columnas[i]) != 0 else 1
            for j in range(len(listas_columnas[i])):
                row_number += 1
                ### COMPUTE THE HORIZONTAL OR VERTICAL AVERAGE (average within the present column or row)
                if average:
                    value = round((listas_columnas[i][j]/valores_filas[j])*100, 3)
                else:
                    value = round((listas_columnas[i][j]/sum_column)*100, 3)
                valores_columnas[keys_columnas[i]][j] = value if str(value) != "nan" else 0 #update the value
                hoja.cell(row_number, cn).value = str(value) + "%" #print the value
            cn += 1

        cnumber = cn

    ### RECALCULATE VALORES_FILAS AGAIN TO GET THE MOST UPDATED DATA
    listas_columnas = list(valores_columnas.values()) #Get the updated version
    if per: #Compute valores_filas again
        valores_filas = []
        for i in range(len_lists):
            valores_filas.append(round(sum([lc[i] for x, lc in enumerate(listas_columnas) if "All" not in keys_columnas[x]]), 3))
    
    ### PRINT THE LAST COLUMN (AVERAGE OR TOTAL)  
    if last_column:
        if last_column_average: #TODO: para qué?
            valores_filas = [round(vf / (len(listas_columnas) - len([c for c in keys_columnas if "All" in c])), 3) for vf in valores_filas]
        ### PRINT THE LAST COLUMN, CONTAINING THE TOTAL OR THE AVERAGE OF THE DATA
        print_averages_total_column(hoja, starting_row, cnumber, valores_filas, average=last_column_average, per = per or ponderate and all(c == "sum" for c in computations_columns))
    
    ### PRINT LAST ROW (TOTAL OR AVERAGE)
    for i, c in enumerate(valores_columnas):
        if average:
            valores_columnas[c] = compute_average(valores_columnas[c], computations_columns[i])
        else: #total
            valores_columnas[c] = round(sum(valores_columnas[c]), 3)

    final_values = list(valores_columnas.values())
    if last_column: # Take the last value computed for the last column (average or total)
        if average:
            final_values.append(round(sum(valores_filas) / len(valores_filas), 3))
        else:
            final_values.append(round(sum(valores_filas), 3))
    data_column = column_number + len_add_info + 2 if total_analysed_column else column_number + len_add_info + 1
    print_averages_total(hoja, last_used_row, final_values, column_number, data_column, average= average, per = per or ponderate and all(c == "sum" for c in computations_columns), exception = exception)
    ###

    return last_used_row + 1, cnumber + 1

def get_groups_add_info(data, row, additional_info):
    if type(additional_info) == list:
        additional_info = [ai for ai in additional_info if ai in list(data.columns) and ai != row]
        groups = [row] + additional_info
        add_info = len(additional_info)
    else: #es un diccionario que indica con la key con quien se tiene que agrupar
        if row in additional_info:
            groups = [row] + additional_info[row]
            add_info = len(additional_info[row])
        else:
            groups = [row]
            add_info = max(len(additional_info[k]) for k in additional_info)
    return groups, add_info

##########################################################################################################
# Function in charge of printting the data, the arguments are the same as the explained in hoja_iValues  #
##########################################################################################################
def row_iteration(hoja, columns, row_number, column_number, data, third_columns, computations_columns, sorting_lists, group = None, first_columns = None, second_columns = None, per = False, average = False, last_column = False, last_column_average = False, 
                columns2 = None, data2 = None, third_columns2 = None, computations_columns2 = None, first_columns2 = None, second_columns2 = None, additional_info = [], ponderate = False):
    all_columns = list(data.columns)
    for row in rows_groups: #Geography, Dramma, Opera, Aria, Label, Composer...
        if row in all_columns or any(sub in all_columns for sub in rows_groups[row][0]):
            forbiden = []
            if group != None:
                forbiden = [forbiden_groups[group[i]] for i in range(len(group))]
                forbiden = [item for sublist in forbiden for item in sublist]
            if group == None or row not in forbiden:
                # 1. Write the Title in Yellow
                hoja.cell(row_number, column_number).value = "Per " + row
                hoja.cell(row_number, column_number).fill = yellowFill
                row_number += 1
                sorting = rows_groups[row][1]
                # 2. Write the information depending on the subgroups (ex: Geography -> City, Country)
                if len(rows_groups[row][0]) == 0: # No subgroups
                    starting_row = row_number
                    data = sort_dataframe(data, row, sorting_lists, sorting) # Sort the dataframe based on the json sorting_lists in Json_extra
                    groups_add_info, add_info = get_groups_add_info(data, row, additional_info)
                    row_number, last_column_used = print_groups(hoja, data.groupby(groups_add_info, sort = False), row_number, column_number, columns, third_columns, computations_columns, first_columns, second_columns, per = per, average=average, last_column = last_column, last_column_average = last_column_average, additional_info = add_info, ponderate = ponderate, not_grouped_df = (groups_add_info, data[groups_add_info+ columns]))
                    if columns2 != None: #Second subgroup
                        groups_add_info, add_info = get_groups_add_info(data, row, additional_info)
                        if data2 is not None:
                            data2 = sort_dataframe(data2, row, sorting_lists, sorting)
                        _,_ = print_groups(hoja, data.groupby(groups_add_info, sort = False) if data2 is None else data2.groupby(groups_add_info, sort = False), starting_row, last_column_used + 1, columns2, third_columns2, computations_columns2, first_columns2, second_columns2, per = per, average=average, last_column = last_column, last_column_average = last_column_average, additional_info = add_info, ponderate = ponderate, not_grouped_df = (groups_add_info, data[groups_add_info + columns]))
                else: #has subgroups, ex: row = Date, subgroups: Year
                    for i, subrows in enumerate(rows_groups[row][0]):
                        if (subrows == None or subrows not in forbiden) and subrows in all_columns:
                            if "Tempo" in subrows:
                                data[subrows] = data[subrows].fillna('')
                            starting_row = row_number
                            sort_method = sorting[i]
                            hoja.cell(row_number, column_number).value = subrows
                            hoja.cell(row_number, column_number).fill = greenFill
                            data = sort_dataframe(data, subrows, sorting_lists, sort_method)
                            
                            groups_add_info, add_info = get_groups_add_info(data, subrows, additional_info)
                            row_number, last_column_used = print_groups(hoja, data.groupby(groups_add_info, sort = False), row_number, column_number, columns, third_columns, computations_columns, first_columns, second_columns, per = per, average=average, last_column = last_column, last_column_average = last_column_average, additional_info = add_info, ponderate = ponderate, not_grouped_df = (groups_add_info, data[groups_add_info + columns]))
                            if columns2 != None: #Second subgroup
                                if "Tempo" in subrows and data2 is not None:
                                    data2[subrows] = data2[subrows].fillna('')
                                if data2 is not None:
                                    data2 = sort_dataframe(data2, subrows, sorting_lists, sort_method)
                                groups_add_info, add_info = get_groups_add_info(data, subrows, additional_info)
                                _,_ = print_groups(hoja, data.groupby(groups_add_info, sort = False) if data2 is None else data2.groupby(groups_add_info, sort = False), starting_row, last_column_used + 1, columns2, third_columns2, computations_columns2, first_columns2, second_columns2, per = per, average=average, last_column = last_column, last_column_average = last_column_average, additional_info = add_info, ponderate = ponderate, not_grouped_df = (groups_add_info, data[groups_add_info+ columns]))
                    
                            row_number += 1
                row_number += 1 
    return row_number

###########################################################################################################################################################
# This function is in charge of printing each iValue's sheet
#
#   hoja: the openpyxl sheet object in which we will write
#   columns: list of the dataframe (grouped) column names that we need to access (as it doesn't necessarily correspond to the names that we want to print)
#   data: main dataframe
#   third_columns: list of the names of the columns that we need to print
#   computations_columns: information about the matematical computation that has to be done to each column (sum, mean...)
#   sorting_lists: dictionary of lists used for sorting the output and showing it in an appropiate way
#   ----------------
#   groups: used for factor > 1
#   first_columns: list of column names to print in first place, along with the number of columns that each has to embrace
#   second_columns: list of column names to print in second place, along with the number of columns that each has to embrace
#   per: boolean value to indicate if we need to compute the excel in absolute values or percentage (by default it is absolute)
#   average: boolean value to indicate if we want the average row at the last group's row
#   last_column: boolean value to indicate if we want a summarize on the last column
#   last_column_average: boolean to indicate if we want the last column to have each row's average (otherwise, the total is writen)
#   ------
#   columns2: names of the second groups of columns (some sheets have subgroupings at the right), used in emphatised_scale_degrees and Intervals_types
#   data2: dataframe used for printing information at the right
#   third_columns2: columns that will be printed
#   computations_columns2: computations for those columns
#   first_columns2: columns printed on first place
#   second_columns2: colummns printed on second place
#   additional_info: list of additional columns
#   ponderate: boolean to indicate if we want to ponderate the data printed or not
#
###########################################################################################################################################################
def hoja_iValues(hoja, columns, data, third_columns, computations_columns, sorting_lists, groups = None, first_columns = None, second_columns = None, per = False, average = False, last_column = False, last_column_average = False, 
                columns2 = None, data2 = None, third_columns2 = None, computations_columns2 = None, first_columns2 = None, second_columns2 = None, additional_info = [], ponderate = False):
    
    row_number = 1 #we start writing in row 1
    column_number = 1
    if groups == None:
        row_iteration(hoja, columns, row_number, column_number, data, third_columns, computations_columns, sorting_lists, first_columns = first_columns, second_columns = second_columns, per = per, 
                        average = average, last_column = last_column, last_column_average = last_column_average, columns2 = columns2, data2 = data2, third_columns2 = third_columns2, computations_columns2 = computations_columns2, first_columns2 = first_columns2, second_columns2 = second_columns2, additional_info = additional_info, ponderate = ponderate)
    else:
        data_grouped = data.groupby(list(groups)) #we may be grouping by more than 2 factors
        
        last_printed = {i:('', 0) for i in range(len(groups))}
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
                        hoja.merge_cells(start_row = last_printed[i][1], start_column = i + 1, end_row = row_number - 2, end_column = i + 1)
                        hoja.cell(last_printed[i][1],  i + 1).fill = factors_Fill[i]
                    
                    last_printed[i] = (g, row_number + 1)
 
                row_number += 1
                cnumber += 1
            data2_grouped = None
            if data2 is not None:
                data2_grouped = data2.groupby(list(groups)).get_group(group if len(group) > 1 else group[0])
            rn = row_iteration(hoja, columns, row_number, cnumber, group_data, third_columns, computations_columns, sorting_lists, group = groups, first_columns = first_columns, second_columns = second_columns, per = per, 
                            average = average, last_column = last_column, last_column_average = last_column_average, columns2 = columns2, data2 = data2_grouped, third_columns2 = third_columns2, computations_columns2 = computations_columns2, first_columns2 = first_columns2, second_columns2 = second_columns2, additional_info = additional_info, ponderate = ponderate)           
            row_number = rn
        #merge last cells
        for i, g in enumerate(group):
            if last_printed[i][0] == g:
                hoja.merge_cells(start_row = last_printed[i][1], start_column = i + 1, end_row = row_number - 2, end_column = i + 1)
                hoja.cell(last_printed[i][1],  i + 1).fill = factors_Fill[i]

########################################
# data frame sorting for rows display  #
########################################
def sort_dataframe(data, column, sorting_lists, key_to_sort):
    if key_to_sort == "Alphabetic":
        dataSorted = data.sort_values(by = [column])
    else:
        form_list = sorting_lists[key_to_sort] # es global
        indexes = []
        for i in data[column]:
            if str(i.lower().strip()) not in ["nan", 'nd']:
                value = i.strip() if key_to_sort not in ['FormSorting', 'RoleSorting'] else i.strip().lower()
                try:
                    index = form_list.index(value)
                except:
                    index = 999
                    logger.warning('We do not have the value {} in the sorting list {}'.format(value, key_to_sort))
                indexes.append(index)
            else:
                indexes.append(999) #at the end of the list
        
        data.loc[:,"Ranks"] = indexes
        dataSorted = data.sort_values(by = ["Ranks"])
        dataSorted.drop("Ranks", 1, inplace = True)
    return dataSorted

########################################################################
# Function that finds the propper name used in our intermediate files  #
########################################################################
def columns_alike_our_data(third_columns_names, second_column_names, first_column_names = None):
    columns = []
    counter_first = 0
    sub_counter_first = 0
    counter_second = 0
    sub_counter_second = 0
    for c in third_columns_names:
        if first_column_names:
            cn = first_column_names[counter_first][0] + second_column_names[counter_second][0] + c
            sub_counter_first += 1
            if sub_counter_first >= first_column_names[counter_first][1]:
                sub_counter_first = 0
                counter_first += 1
        else:
            cn = second_column_names[counter_second][0] + c
        sub_counter_second += 1
        if sub_counter_second >=second_column_names[counter_second][1]:
            sub_counter_second  = 0
            counter_second += 1
        columns.append(cn)
    return columns

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
def iValues(data, results_path, name, sorting_lists, visualiser_lock, additional_info = [], remove_columns = False, groups = None):
    try:
        workbook = openpyxl.Workbook()

        #HOJA 1: STATISTICAL_VALUES
        column_names = ["Total analysed", "Intervallic ratio", "Trimmed intervallic ratio", "dif. Trimmed", "% Trimmed", "Absolute intervallic ratio", "Std", "Absolute Std", 'Syllabic ratio']
        computations = ['sum'] + ["mean"]*(len(column_names) - 1) #HAREMOS LA MEDIA DE TODAS LAS COLUMNAS
        hoja_iValues(workbook.create_sheet("Statistical_values"), column_names, data, column_names, computations, sorting_lists, groups = groups, average=True, additional_info = additional_info, ponderate = True)
        
        #HOJA 2: AMBITUS
        first_column_names = [("", 1), ("Lowest", 2), ("Highest", 2), ("Lowest", 2), ("Highest", 2), ("Ambitus", 8)] if not remove_columns else [("", 1),("Lowest", 2), ("Highest", 2), ("Ambitus", 2)]

        second_column_names = [("", 5), ("Mean", 2), ("Mean", 2), ("Largest", 2), ("Smallest", 2), ("Absolute", 2), ("Mean", 2)] if not remove_columns else [("", 5), ("Largest", 2)]

        third_columns_names = ["Total analysed","Note", "Index", "Note", "Index", "Note", "Index", "Note", "Index","Semitones", "Interval","Semitones", "Interval", "Semitones", "Interval","Semitones", "Interval"] if not remove_columns else ["Total analysed","Note", "Index", "Note", "Index","Semitones", "Interval"]

        computations = ["sum","minNote", "min", "maxNote", "max", 'meanNote', 'mean','meanNote', 'mean','max', "maxInterval", 'min', "minInterval",'absolute', 'absoluteInterval', "meanSemitones", "meanInterval"] if not remove_columns else ["sum", "minNote", "min", "maxNote", "max", 'max', "maxInterval"]

        columns = columns_alike_our_data(third_columns_names, second_column_names, first_column_names)

        hoja_iValues(workbook.create_sheet("Ambitus"), columns, data, third_columns_names, computations, sorting_lists, groups = groups, first_columns=first_column_names, second_columns=second_column_names, average=True, additional_info = additional_info)

        #HOJA 3: LARGEST_LEAPS
        second_column_names = [("", 1), ("Ascending", 2), ("Descending", 2)]
        third_columns_names = ["Total analysed","Semitones", "Interval", "Semitones", "Interval"]
        columns = columns_alike_our_data(third_columns_names, second_column_names)
        computations = ["sum", "max", "maxInterval", "min", "minInterval"]

        hoja_iValues(workbook.create_sheet("Largest_leaps"), columns, data, third_columns_names, computations, sorting_lists, groups = groups, second_columns=second_column_names, average=True, additional_info = additional_info)

        if "Sheet" in workbook.get_sheet_names(): # Delete the default sheet
            std=workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        with visualiser_lock:
            # VISUALISATIONS
            columns_visualisation = ['Intervallic ratio', 'Trimmed intervallic ratio', 'Std']
            if groups:
                data_grouped = data.groupby(list(groups))
                for g, datag in data_grouped:
                    result_visualisations = path.join(results_path, 'visualisations', g)
                    if not os.path.exists(result_visualisations):
                        os.mkdir(result_visualisations)

                    name_bar = path.join(result_visualisations, name.replace('.xlsx', '.png'))
                    ivalues_bar_plot(name_bar, datag, columns_visualisation, second_title = str(g))
                    name_box = path.join(result_visualisations, 'Ambitus' + name.replace('.xlsx', '.png'))
                    box_plot(name_box, datag, second_title = str(g))
            else:
                name_bar = results_path + path.join('visualisations', name.replace('.xlsx', '.png'))
                ivalues_bar_plot(name_bar, data, columns_visualisation)
                name_box = path.join(results_path, 'visualisations', 'Ambitus' + name.replace('.xlsx', '.png'))
                box_plot(name_box, data)
    except Exception as e:
        logger.error('{}   Problem found:'.format(name), exc_info=True)
        
#######################################################################################
# Function used to generate the files 2a.Intervals, 2a.Intervals_absolute and 5.Clefs #
#######################################################################################
def iiaIntervals(data, name, sorting_list, results_path, sorting_lists, visualiser_lock, additional_info = [], groups = None):
    try:
        workbook = openpyxl.Workbook()
        all_columns = data.columns.tolist()
        general_cols = copy.deepcopy(not_used_cols)
        for row in rows_groups:
            if len(rows_groups[row][0]) == 0:
                general_cols.append(row)
            else:
                general_cols += rows_groups[row][0]
        
        third_columns_names_origin = set(all_columns) - set(general_cols) #nombres de todos los intervalos
        third_columns_names_origin = sort(third_columns_names_origin, sorting_list)
        third_columns_names = ['Total analysed'] + third_columns_names_origin

        computations = ["sum"]*len(third_columns_names) # esta hoja va de sumar, así que en todas las columnas el cómputo que hay que hacer es sumar!

        hoja_iValues(workbook.create_sheet("Weighted"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups = groups, average=True,last_column=True, last_column_average = False,additional_info = additional_info, ponderate=True)
        hoja_iValues(workbook.create_sheet("Horizontal Per"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups = groups,per = True, average=True, last_column=True, last_column_average = False, additional_info = additional_info)
        hoja_iValues(workbook.create_sheet("Vertical Per"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups = groups,per = True, average = False, last_column=True, last_column_average = True, additional_info = additional_info)
        
        if "Sheet" in workbook.get_sheet_names(): # Delete the default sheet
            std=workbook.get_sheet_by_name('Sheet')
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
                    result_visualisations = path.join(results_path, 'visualisations', g)
                    if not os.path.exists(result_visualisations):
                        os.mkdir(result_visualisations)

                    name_bar = path.join(result_visualisations, name.replace('.xlsx', '.png'))
                    bar_plot(name_bar, datag, third_columns_names_origin, 'Intervals' if 'Clef' not in name else 'Clefs', title, second_title = str(g))
            else:
                name_bar = path.join(results_path, 'visualisations', name.replace('.xlsx', '.png'))
                bar_plot(name_bar, data, third_columns_names_origin, 'Intervals' if 'Clef' not in name else 'Clefs', title)
    except Exception as e:
        logger.error('{}  Problem found:'.format(name), exc_info=True)

#########################################################
# Function to generate the file 3.Intervals_types.xlsx  #
#########################################################
def IIIIntervals_types(data, results_path, name, sorting_lists, visualiser_lock, groups = None, additional_info = []):
    try:
        workbook = openpyxl.Workbook()
        
        second_column_names = [("", 2), ("Leaps", 3), ("StepwiseMotion", 3)]
        second_column_names2 = [('', 1), ("Perfect", 3), ("Major", 3), ("Minor", 3), ("Augmented", 3), ("Diminished", 3)]
        third_columns_names = ['Total analysed', "RepeatedNotes", "Ascending", "Descending", "All", "Ascending", "Descending", "All"] 
        third_columns_names2 = ['Total analysed', "Ascending", "Descending", "All", "Ascending", "Descending", "All", "Ascending", "Descending", "All", "Ascending", "Descending", "All", "Ascending", "Descending", "All"]
        computations = ["sum"]*len(third_columns_names)
        computations2 = ['sum']*len(third_columns_names2)
        columns = columns_alike_our_data(third_columns_names, second_column_names)
        columns2 = columns_alike_our_data(third_columns_names2, second_column_names2)

        hoja_iValues(workbook.create_sheet("Weighted"), columns, data, third_columns_names, computations, sorting_lists, groups = groups, last_column=True, last_column_average = False, second_columns=second_column_names, average=True,
                    columns2 = columns2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, additional_info = additional_info, ponderate=True)
        hoja_iValues(workbook.create_sheet("Horizontal Per"), columns, data, third_columns_names, computations, sorting_lists, groups = groups, second_columns=second_column_names, per = True, average=True, last_column=True, last_column_average = False,
                    columns2 = columns2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, additional_info = additional_info)
        hoja_iValues(workbook.create_sheet("Vertical Per"), columns, data, third_columns_names, computations, sorting_lists, groups = groups, second_columns=second_column_names, per = True, average = False, last_column=True, last_column_average = True,
                    columns2 = columns2,  third_columns2=third_columns_names2, computations_columns2=computations2, second_columns2=second_column_names2, additional_info = additional_info)

        #borramos la hoja por defecto
        if "Sheet" in workbook.get_sheet_names():
            std=workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        with visualiser_lock:
            #VISUALISATIONS
            if groups:
                data_grouped = data.groupby(list(groups))
                for g, datag in data_grouped:
                    result_visualisations = path.join(results_path, 'visualisations', g)
                    if not os.path.exists(result_visualisations):
                        os.mkdir(result_visualisations)

                    name1 = path.join(result_visualisations, name.replace('.xlsx',  '') + '_AD.png')
                    pie_plot(name1, datag, second_title = str(g))
                    name2 = path.join(result_visualisations, name.replace('.xlsx',  '.png'))
                    double_bar_plot(name2, data, second_title = str(g))
            else:
                name1 = path.join(results_path, 'visualisations', name.replace('.xlsx', '') + '_AD.png')
                pie_plot(name1, data)
                name2 = path.join(results_path, 'visualisations', name.replace('.xlsx',  '.png'))
                double_bar_plot(name2, data)
    except Exception as e:
        logger.error('3Interval_types  Problem found:', exc_info=True)

########################################################################
# Function to generate the files 4xEmphasised_scale_degrees.xlsx
########################################################################
def emphasised_scale_degrees(data, sorting_list, name, results_path, sorting_lists, visualiser_lock, groups = None, additional_info = []):
    try:
        workbook = openpyxl.Workbook()
        all_columns = data.columns.tolist()
        general_cols = copy.deepcopy(not_used_cols)
        for row in rows_groups:
            if len(rows_groups[row][0]) == 0:
                general_cols.append(row)
            else:
                general_cols += rows_groups[row][0]
        
        third_columns_names_origin = list(set(all_columns) - set(general_cols)) #nombres de todos los intervalos
        third_columns_names_origin = sort(third_columns_names_origin, sorting_list)
        third_columns_names = ['Total analysed'] + third_columns_names_origin
        third_columns_names2 = ['Total analysed'] + ['1', '4', '5', '7', 'Others']

        computations = ["sum"]*len(third_columns_names) # esta hoja va de sumar, así que en todas las columnas el cómputo que hay que hacer es sumar!
        computations2 = ["sum"]*len(third_columns_names2)

        emphdegrees = pd.DataFrame(prepare_data_emphasised_scale_degrees_second(data, third_columns_names, third_columns_names2))
        data2 = pd.concat([data[[gc for gc in general_cols if gc in all_columns]], emphdegrees], axis = 1)
        _, unique_columns = np.unique(data2.columns, return_index=True)
        data2 = data2.iloc[:, unique_columns]
        hoja_iValues(workbook.create_sheet("Wheighted"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, last_column=True,last_column_average=False,average=True,
                    columns2=third_columns_names2,  data2 = data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info, ponderate=True)
        hoja_iValues(workbook.create_sheet("Horizontal Per"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, per=True, average=True, last_column=True, last_column_average=False,
                    columns2=third_columns_names2,  data2 = data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info)
        hoja_iValues(workbook.create_sheet("Vertical Per"), third_columns_names, data, third_columns_names, computations, sorting_lists, groups=groups, per=True, average=False, last_column=True, last_column_average=True,
                    columns2=third_columns_names2,  data2 = data2, third_columns2=third_columns_names2, computations_columns2=computations2, additional_info=additional_info)
        
        #Delete the default sheet
        if "Sheet" in workbook.get_sheet_names():
            std=workbook.get_sheet_by_name('Sheet')
            workbook.remove_sheet(std)
        workbook.save(os.path.join(results_path, name))

        with visualiser_lock:
            subtitile = 'in relation to the global key' if '4a' in name else 'in relation to the local key'
            #VISUALISATIONS
            if groups:
                data_grouped = data.groupby(list(groups))
                for g, datag in data_grouped:
                    result_visualisations = path.join(results_path, 'visualisations', g)
                    if not os.path.exists(result_visualisations):
                        os.mkdir(result_visualisations)

                    name1 = path.join(result_visualisations, '4a.Scale_degrees_GlobalKey.png' if '4a' in name else '4b.scale_degrees_LocalKey.png')
                    customized_plot(name1, data, third_columns_names_origin, subtitile, second_title=g)
            else:
                name1 = path.join(results_path, 'visualisations', '4a.scale_degrees_GlobalKey.png' if '4a' in name else '4b.scale_degrees_LocalKey.png')
                customized_plot(name1, data, third_columns_names_origin, subtitile)

    except Exception as e:
        logger.error('{}  Problem found:'.format(name), exc_info=True)

#####################################################################
# Function made for sorting the first list based on the second one  #
#####################################################################
def sort(list_to_sort, main_list):
    indexes = []
    huerfanos = []
    for i in list_to_sort:
        if i in main_list:
            indexes.append(main_list.index(i))
        else:
            huerfanos.append(i)
            logger.warning('We do not have the appropiate sorting for {}'.format(i))
    indexes = sorted(indexes)
    list_sorted = [main_list[i] for i in indexes]
    return list_sorted + huerfanos

#######################################
# This function combines the 3 lists  #
#######################################
def get_lists_combined(first_element, second_list, third_list):
    final_list = []
    
    for s in third_list:
        if second_list != '': #ocurre en las combinaciones de un elemento
            final_list.append(first_element + ',' + second_list + ',' + s)
        else:
            final_list.append(first_element + ',' + s)

    return final_list

########################################################################################################
# This function returns the second group of data that we need to show, regarding third_columns_names2  #
########################################################################################################
def prepare_data_emphasised_scale_degrees_second(data, third_columns_names, third_columns_names2):
    data2 = {}
    rest_data = set(third_columns_names) - set(third_columns_names2 + ['#7'])

    for name in third_columns_names2:
        column_data = []
        if name == '7': #sumamos las columnas 7 y #7
            seven = data[name]
            if '#7' in data.columns:
                hastagseven = data["#7"]
                column_data = [np.nansum([seven.tolist()[i], hastagseven.tolist()[i]]) for i in range(len(seven))]
            else:
                column_data = seven.tolist()
        elif name == "Others": #sumamos todas las columnas de data menos 1, 4, 5, 7, #7
            column_data = data[rest_data].sum(axis = 1).tolist()
        else:
            column_data = data[name].tolist()
        data2[name] = pd.Series(column_data)
    return data2

########################################################################################
# This function returns the dictionary with the lists used to sort every group of data #
########################################################################################
def get_sorting_lists():
    RoleSorting = general_sorting.get_role_sorting() # Only valid for DIDONE corpus
    FormSorting = general_sorting.get_form_sorting()
    KeySorting = general_sorting.get_key_sorting()
    KeySignatureSorting = general_sorting.get_KeySignature_sorting()
    KeySignatureGroupedSorted = general_sorting.get_KeySignatureType_sorting()
    TimeSignatureSorting = general_sorting.get_TimeSignature_sorting()
    TempoSorting = general_sorting.get_Tempo_sorting()
    TempoGroupedSorting1 = general_sorting.get_TempoGrouped1_sorting()
    TempoGroupedSorting2 = general_sorting.get_TempoGrouped2_sorting()
    clefs = general_sorting.get_Clefs_sorting()
    scoring_sorting = general_sorting.get_scoring_sorting() #Long combination
    scoring_family = general_sorting.get_familiesCombinations_sorting()
    Intervals = melody_sorting.intervals_sorting()
    Intervals_absolute = melody_sorting.intervals_absolutte_sorting()
    scale_degrees = melody_sorting.MelodicDegrees_sorting()
    
    return {"RoleSorting": [i.lower() for i in RoleSorting],
            "FormSorting": [i.lower() for i in FormSorting],
            "KeySorting": KeySorting,
            "KeySignatureSorting": KeySignatureSorting,
            "KeySignatureGroupedSorted": KeySignatureGroupedSorted,
            "TimeSignatureSorting": TimeSignatureSorting,
            "TempoSorting": TempoSorting + [''], #a veces algunas puede ser nan, ya que no tienen tempo mark, las nan las ponemos al final
            "TempoGroupedSorting1": TempoGroupedSorting1 + [''],
            "TempoGroupedSorting2": TempoGroupedSorting2 + [''],
            "Intervals": Intervals,
            "Intervals_absolute": Intervals_absolute,
            "Clefs": clefs,
            "ScoringSorting": scoring_sorting,
            "ScoringFamilySorting": scoring_family,
            "ScaleDegrees": scale_degrees,
            }

##################################################################################################
# This function transforms the interval into absolute values, adding the ascending and descending#
##################################################################################################
def make_intervals_absolute(intervals_info):
    intervals_info_columns = intervals_info.columns
    columns_to_merge = [iname for iname in intervals_info_columns if '-' in iname]
    new_columns = [iname.replace('-','') for iname in columns_to_merge]
    intervals_info_abs = pd.DataFrame()
    intervals_info_abs = pd.concat([intervals_info, intervals_info_abs], axis = 1)
    for i, c in enumerate(new_columns):
        column_deprecated = intervals_info_abs[columns_to_merge[i]].tolist()
        x = np.nan_to_num(column_deprecated)
        if c in intervals_info_abs:
            y = np.nan_to_num(intervals_info_abs[c])
            intervals_info_abs[c] = list(np.add(x, y))
        else:
            intervals_info_abs[c] = list(x)
        intervals_info_abs = intervals_info_abs.drop(columns_to_merge[i], axis = 1)
    return intervals_info_abs

def remove_folder_contents(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            remove_folder_contents(file_path)

#####################################################################
# Function that generates the needed information for each grouping  #
#####################################################################
def group_execution(groups, results_path_factorx, additional_info, i, sorting_lists, all_info, intervals_info, absolute_intervals, intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info, sequential):
    if groups != []:
        if sequential:
            print(groups)
        results_path = path.join(results_path_factorx, '_'.join(groups))
        if not os.path.exists(results_path):
            os.mkdir(results_path)
    else:
        results_path = results_path_factorx
    if os.path.exists(path.join(results_path, 'visualisations')):
        remove_folder_contents(path.join(results_path, 'visualisations'))
    else:
        os.mkdir(path.join(results_path, 'visualisations'))
    # MUTITHREADING
    try:
        executor = concurrent.futures.ThreadPoolExecutor()
        visualiser_lock = threading.Lock()
        futures = []
        if not all_info.empty:
            futures.append(executor.submit(iValues, all_info, results_path, '-'.join(groups) + "_1Values.xlsx", sorting_lists, visualiser_lock, additional_info, True if i == 0 else False, groups if groups != [] else None))
        if not intervals_info.empty:
            futures.append(executor.submit(iiaIntervals, intervals_info, '-'.join(groups) + "_2aIntervals.xlsx", sorting_lists["Intervals"], results_path, sorting_lists, visualiser_lock, additional_info, groups if groups != [] else None))
            futures.append(executor.submit(iiaIntervals, absolute_intervals, '-'.join(groups) + "_2bIntervals_absolute.xlsx", sorting_lists["Intervals_absolute"], results_path, sorting_lists, visualiser_lock, additional_info, groups if groups != [] else None))
        if not intervals_types.empty:
            futures.append(executor.submit(IIIIntervals_types, intervals_types, results_path,'-'.join(groups) + "_3Interval_types.xlsx", sorting_lists, visualiser_lock, groups if groups != [] else None, additional_info))
        if not emphasised_scale_degrees_info_A.empty:
            futures.append(executor.submit(emphasised_scale_degrees, emphasised_scale_degrees_info_A, sorting_lists["ScaleDegrees"], '-'.join(groups) + "_4aScale_degrees.xlsx", results_path, sorting_lists, visualiser_lock, groups if groups != [] else None, additional_info))
        if not emphasised_scale_degrees_info_B.empty:
            futures.append(executor.submit(emphasised_scale_degrees, emphasised_scale_degrees_info_B, sorting_lists["ScaleDegrees"], '-'.join(groups) + "_4bScale_degrees_relative.xlsx", results_path, sorting_lists, visualiser_lock, groups if groups != [] else None, additional_info))
        if not clefs_info.empty:
            futures.append(executor.submit(iiaIntervals, clefs_info, '-'.join(groups) + "_5Clefs.xlsx", sorting_lists["Clefs"], results_path, sorting_lists, visualiser_lock, additional_info, groups if groups != [] else None))

        #wait for all
        if sequential:
            kwargs = {'total': len(futures),'unit': 'it','unit_scale': True,'leave': True}
            for f in tqdm(concurrent.futures.as_completed(futures), **kwargs):
                pass
        else:
            for f in concurrent.futures.as_completed(futures):
                pass
    except KeyboardInterrupt:
        sys.exit(2)
    except Exception as e:
        pass

###################################################################################################
# Function that generates all the files for each factor (choosed by the user or up to 1 by default)
#
# all_dataframes: list with all the needed dataframes
# main_results_path: path to the folder where the results will be stored
# i: number of factors
###################################################################################################
def factor_execution(all_dataframes, main_results_path, i, sorting_lists, sequential=True):
    global rows_groups
    global not_used_cols
    rg = copy.deepcopy(rows_groups)
    nuc = copy.deepcopy(not_used_cols)

    # 1. Split all the dataframes to work individually
    all_info, intervals_info, clefs_info, intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B = all_dataframes
    all_info = all_info.dropna(how='all', axis=1)
    intervals_info= intervals_info.dropna(how='all', axis=1)
    intervals_types= intervals_types.dropna(how='all', axis=1)
    emphasised_scale_degrees_info_A= emphasised_scale_degrees_info_A.dropna(how='all', axis=1)
    emphasised_scale_degrees_info_B= emphasised_scale_degrees_info_B.dropna(how='all', axis=1)
    clefs_info= clefs_info.dropna(how='all', axis=1)
    print(str(i) + " factor")

    # 2. Get the additional_info dictionary (special case if there're no factors)
    additional_info = {"Label":["Aria"], "Aria":['Label']} #solo agrupa aria
    if i == 0:
        rows_groups = {"Id": ([], "Alphabetic")}
        rg_keys = [rg[r][0] if rg[r][0] != [] else r for r in rg]
        for r in rg_keys:
            if type(r) == list:
                not_used_cols += r
            else:
                not_used_cols.append(r)
        additional_info = ["Label", "Aria", "Composer", "Year"] #It a list, so it is applicable to all grouppings
    
    rg_groups = [[]] 
    if i >= 2:
        rg_groups = list(permutations(list(forbiden_groups.keys()), i - 1))[4:]

        if i > 2:
            prohibidas = ['Composer', 'Opera']
            for g in rg_groups:
                if 'Aria' in g:
                    g_rest = g[g.index('Aria'):]
                    if any(p in g_rest for p in prohibidas):
                        rg_groups.remove(g)
                elif 'Label' in g:
                    g_rest = g[g.index('Label'):]
                    if any(p in g_rest for p in prohibidas):
                        rg_groups.remove(g)
        rg_groups = [r for r in rg_groups if r[0] in list(all_info.columns)]

    results_path_factorx = path.join(main_results_path, str(i) + " factor") if i > 0 else path.join(main_results_path, "Data")
    if not os.path.exists(results_path_factorx):
        os.mkdir(results_path_factorx)

    absolute_intervals = make_intervals_absolute(intervals_info)

    # MULTIPROCESSING (one process per group (year, decade, city, country...))
    if sequential: # 0 and 1 factors
        for groups in rg_groups:
            group_execution(groups, results_path_factorx, additional_info, i, sorting_lists, all_info, intervals_info, absolute_intervals, intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info, sequential) 
            rows_groups = rg
            not_used_cols = nuc
    else: # from 2 factors
        process_executor = concurrent.futures.ProcessPoolExecutor()
        futures = [process_executor.submit(group_execution, groups, results_path_factorx, additional_info, i, sorting_lists, all_info, intervals_info, absolute_intervals, intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B, clefs_info, sequential) for groups in rg_groups]
        kwargs = {'total': len(futures),'unit': 'it','unit_scale': True,'leave': True} 
        for f in tqdm(concurrent.futures.as_completed(futures), **kwargs): 
            rows_groups = rg
            not_used_cols = nuc

######################################################################################################
# Function used for printing the information in the corresponding excel files
#
# all_dataframes: list of the different intermediate dataframes obtained after the reading module
# results_path: path to the folder in which the excels will be generated
# num_factors: maximum number of factors to be generated
######################################################################################################
def write(all_dataframes, results_path, num_factors_max, sequential=False):  
    # 1. Get the sorting variables to print the information in a proper way
    path_sorting_lists = os.path.join(os.getcwd(), 'source', 'Json_extra', "sorting_lists.json")
    if os.path.exists(path_sorting_lists):
        sorting_lists = json.load(open(path_sorting_lists))
    else:
        sorting_lists = get_sorting_lists()
        json.dump(sorting_lists, open(path_sorting_lists, "w"), indent=4)
    
    # 2. Start the factor generation
    for i in range(0, num_factors_max + 1):
        factor_execution(all_dataframes, results_path, i, sorting_lists, sequential if i >= 2 else True)
    