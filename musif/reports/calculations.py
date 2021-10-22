import copy
import math
import os
from typing import Dict

import numpy as np
import pandas as pd
from music21 import interval, note, pitch
from musif.common.sort import sort

from .constants import not_used_cols, rows_groups


def note_mean(pitch_ps: list, round_mean: bool =False) -> str:
    mean_pitch = np.nansum(pitch_ps) / len(pitch_ps)
    mean_pitch = mean_pitch if not round_mean else round(mean_pitch)
    if type(mean_pitch) == int or mean_pitch.is_integer():
        p = pitch.Pitch()
        p.ps = mean_pitch
        value = p.nameWithOctave.replace('-', 'b')
    else:
        pitch_up = pitch.Pitch()
        pitch_down = pitch.Pitch()
        if str(mean_pitch) !='nan':
            pitch_up.ps = math.ceil(mean_pitch)
            pitch_down.ps = math.floor(mean_pitch)
            value = "-".join([pitch_up.nameWithOctave.replace('-', 'b'),
                            pitch_down.nameWithOctave.replace('-', 'b')])
        else:
            value=0.0
    return value


def interval_mean(interval_semitones: list) -> str:
    if interval_semitones:
        mean_semitones = np.nansum(interval_semitones) / len(interval_semitones)
        if mean_semitones.is_integer():
            i = interval.convertSemitoneToSpecifierGeneric(mean_semitones)
            value = str(i[0]) + str(i[1])
        else:
            i_up = math.ceil(mean_semitones)
            i_down = math.floor(mean_semitones)
            nup = interval.convertSemitoneToSpecifierGeneric(i_up)
            ndown = interval.convertSemitoneToSpecifierGeneric(i_down)
            value = "-".join([str(nup[0]) + str(nup[1]),
                            str(ndown[0]) + str(ndown[1])])
    else:
        value=0.0
    return value

def compute_value(column_data, computation, ponderate_data, not_grouped_information, ponderate, extra_info=None):
    value = 0
    i=0
 
    try:
        if computation == "mean":
            if not ponderate:
                value = round(np.nansum(column_data) /
                            len([i for i in column_data if str(i) != 'nan']), 3)
            else:
                s = 0
                for v, w in zip(column_data, ponderate_data):
                    if str(v)=='nan':
                        v=0.0
                    s += v * w
                value = round(s / sum(ponderate_data), 3)
        elif computation in ["mean_density","mean_texture"]:
            value = round(np.nansum(column_data) / np.nansum(extra_info), 3)
        elif computation == "min":
            value = min(column_data)
        elif computation == "max":
            value = max(column_data)  
        elif computation == "minNote":
            pitch_ps = [pitch.Pitch(n).ps if str(n) != 'nan' else np.nan for n in column_data]
            min_ps = min(pitch_ps)
            value = column_data.tolist()[pitch_ps.index(min_ps)]
        elif computation == "maxNote":
            pitch_ps = [pitch.Pitch(n).ps if str(n) != 'nan' else np.nan for n in column_data]
            max_ps = max(pitch_ps)
            value = column_data.tolist()[pitch_ps.index(max_ps)]
        elif computation == "meanNote":
            pitch_ps =[pitch.Pitch(n).ps if str(n) != 'nan' else np.nan for n in column_data]
            value = note_mean(pitch_ps)
        elif computation == "minInterval":
            interval_semitones = [interval.Interval(n).semitones if str(n) != 'nan' else np.nan for n in column_data]
            min_sem = min(interval_semitones)
            value = column_data.tolist()[interval_semitones.index(min_sem)]
        elif computation == "maxInterval":
            interval_semitones = [interval.Interval(n).semitones if str(n) != 'nan' else np.nan for n in column_data]
            max_sem = max(interval_semitones)
            value = column_data.tolist()[interval_semitones.index(max_sem)]
        elif computation == "meanInterval" or computation == "meanSemitones":
            lowest_notes_names = [str(a).split(',')[0] for a in column_data]
            max_notes_names = [str(a).split(',')[1] if str(a) != 'nan' else np.nan for a in column_data]
            min_notes_pitch = [pitch.Pitch(a).ps if str(a) != 'nan' else np.nan for a in lowest_notes_names]
            max_notes_pitch = [pitch.Pitch(a).ps if str(a) != 'nan' else np.nan for a in max_notes_names]
            mean_min = note_mean(min_notes_pitch, round_mean = True)
            mean_max = note_mean(max_notes_pitch, round_mean = True)
            i = interval.Interval(noteStart = note.Note(mean_min), noteEnd = note.Note(mean_max))
            if computation == "meanInterval":
                value = i.name
            else:
                value = i.semitones
        elif computation == "absoluteInterval" or computation == "absolute":
            lowest_notes_names = [str(a).split(',')[0] for a in column_data]
            max_notes_names = [str(a).split(',')[1] if str(a) != 'nan' else np.nan for a in column_data]
            min_notes_pitch = [pitch.Pitch(a).ps if str(a) != 'nan' else np.nan for a in lowest_notes_names]
            max_notes_pitch = [pitch.Pitch(a).ps if str(a) != 'nan' else np.nan for a in max_notes_names]
            minimisimo = min(min_notes_pitch)
            maximisimo = max(max_notes_pitch)
            if not (str(minimisimo) or str(maximisimo)) =='nan':
                noteStart = note.Note(lowest_notes_names[min_notes_pitch.index(minimisimo)])
                noteEnd = note.Note(max_notes_names[max_notes_pitch.index(maximisimo)])
                i = interval.Interval(noteStart = noteStart, noteEnd = noteEnd)
                if computation == "absoluteInterval":
                    value = i.name
                else:
                    value = i.semitones
            else:
                noteStart = np.nan
                noteEnd = np.nan
                value = np.nan
        elif computation == "sum":
            value = np.nansum(column_data)
            # PONDERATE WITH THE TOTAL ANALYSED IN THAT ROW
            if ponderate and value != 0 and column_data.name != "Total analysed":
                values = []
                # not_grouped_information needed for adding all the elements in total
                for i in range(len(column_data.tolist())):
                    all_columns = not_grouped_information.columns.tolist()
                    total_intervals = np.nansum([float(not_grouped_information.iloc[i, c]) for c in range(len(all_columns)) if 'All' not in all_columns[c]])
                    intervals = column_data.tolist()[i]
                    values.append(
                        (intervals * ponderate_data[i]) / total_intervals)

                value = np.nansum(values) / sum(ponderate_data)
                value = round(value * 100, 3)

    except ValueError:
        value=np.nan
    if isinstance(value, (int, float)):
        if np.isnan(value):
            value = 0.0
    return value

#####################################################################################
# Function to compute the average in every kind of variable, based on a computation #
#####################################################################################

def compute_average(dic_data: Dict, computation: str):
    value = 0
    computation = computation.replace('_density', '').replace('_texture', '') #In case we have averages for densities or textures we compute normal average 
    try:
        if computation in ["mean", "min", "sum", "max", "absolute","meanSemitones"]:
            value = round(np.nansum(dic_data) / len(dic_data), 3)
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
        
        # value = round(np.nansum(dic_data) / (len(dic_data) - len([z for z in dic_data if z == 0])), 3)
    except ZeroDivisionError or ValueError:
        value = 0.0
    return value

##################################################################################################
# This function transforms the interval into absolute values, adding the ascending and descending#
##################################################################################################

def make_intervals_absolute(intervals_info):
    intervals_info_columns = intervals_info.columns
    columns_to_merge = [
        iname for iname in intervals_info_columns if '-' in iname]
    new_columns = [iname.replace('-', '') for iname in columns_to_merge]
    intervals_info_abs = pd.DataFrame()
    intervals_info_abs = pd.concat(
        [intervals_info, intervals_info_abs], axis=1)
    for i, c in enumerate(new_columns):
        column_deprecated = intervals_info_abs[columns_to_merge[i]].tolist()
        x = np.nan_to_num(column_deprecated)
        if c in intervals_info_abs:
            y = np.nan_to_num(intervals_info_abs[c])
            intervals_info_abs[c] = list(np.add(x, y))
        else:
            intervals_info_abs[c] = list(x)
        intervals_info_abs = intervals_info_abs.drop(
            columns_to_merge[i], axis=1)
    return intervals_info_abs

    ########################################################################
