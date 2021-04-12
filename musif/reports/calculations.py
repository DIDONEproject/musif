import copy
import os
import numpy as np
import pandas as pd
import math
from music21 import pitch, interval, note
from .constants import not_used_cols, rows_groups
import openpyxl
from musif.common.sort import sort
import logging
from .visualisations import *


def note_mean(pitch_ps, round_mean=False):
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
        value = "-".join([pitch_up.nameWithOctave.replace('-', 'b'),
                          pitch_down.nameWithOctave.replace('-', 'b')])
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
        value = "-".join([str(nup[0]) + str(nup[1]),
                          str(ndown[0]) + str(ndown[1])])
    return value

###############################################################################################
# Function used to carry out every kind of computation needed, as determined by 'computation'
###############################################################################################


def compute_value(column_data, computation, ponderate_data, not_grouped_information, ponderate, extra_info=None):
    value = 0
    if computation == "mean":
        if not ponderate:
            # value = round(sum(column_data) / len(column_data), 3)
            value = round(np.nansum(column_data) /
                          len([i for i in column_data if str(i) != 'nan']), 3)
        else:
            s = 0
            for v, w in zip(column_data, ponderate_data):
                s += v * w
            value = round(s / sum(ponderate_data), 3)
    elif computation == ("mean_density" or "mean_texture"):
        value = round(np.nansum(column_data) / np.nansum(extra_info), 3)
    elif computation == "sum":
        value = np.nansum(column_data)
        # PONDERATE WITHT THE TOTAL ANALYSED IN THAT ROW
        if ponderate and value != 0 and column_data.name != "Total analysed":
            values = []
            # not_grouped_information needed for adding all the elements in total
            for i in range(len(column_data.tolist())):
                all_columns = not_grouped_information.columns.tolist()
                total_intervals = np.nansum([not_grouped_information.iloc[i, c] for c in range(
                    len(all_columns)) if 'All' not in all_columns[c]])
                intervals = column_data.tolist()[i]
                values.append(
                    (intervals * ponderate_data[i]) / total_intervals)

            value = np.nansum(values) / sum(ponderate_data)
            value = round(value * 100, 3)
    if np.isnan(value):
        value = 0.0
    return value

#####################################################################################
# Function to compute the average in every kind of variable, based on a computation #
#####################################################################################


def compute_average(dic_data, computation):
    value = 0
    computation = computation.replace('_density', '')
    computation = computation.replace('_texture', '')
    if computation in ["mean", "min", "sum", "max", "absolute", "meanSemitones"]:
        # value = round(sum(dic_data) / len(dic_data), 3)
        value = round(np.nansum(dic_data) / (len(dic_data) -
                                             len([z for z in dic_data if z == 0])), 3)

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
