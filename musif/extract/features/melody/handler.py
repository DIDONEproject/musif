from collections import Counter
from itertools import groupby
from statistics import mean, stdev
from typing import List, Tuple, Dict, Union

import numpy as np
import pandas as pd
from music21.interval import Interval
from scipy.stats import kurtosis, skew
from scipy.stats.mstats import trimmed_mean, trimmed_std

from musif.cache import hasattr
from musif.common._utils import extract_digits
from musif.config import ExtractConfiguration
from musif.extract.common import _mix_data_with_precedent_data
from musif.extract.constants import DATA_PART_ABBREVIATION, DATA_SOUND_ABBREVIATION
from musif.extract.features.core.constants import DATA_INTERVALS
from musif.extract.features.prefix import (
    get_part_feature,
    get_part_prefix,
    get_score_prefix,
    get_sound_prefix,
)

from .constants import *


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    intervals = part_data[DATA_INTERVALS]

    part_features.update(get_motion_features(part_data))
    part_features.update(get_interval_features(intervals))
    part_features.update(get_interval_count_features(intervals))
    part_features.update(get_interval_type_features(intervals))
    part_features.update(get_interval_stats_features(intervals))


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    if len(parts_data) == 0:
        return

    features = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]
        for step in MOTION_STEPS:
            for win in MOTION_WINS:
                if step > win:
                    continue
                key_postfix = _motion_postfix(step, win)
                features[
                    get_part_feature(part, SPEED_AVG_ABS + key_postfix)
                ] = part_features[SPEED_AVG_ABS + key_postfix]
                features[
                    get_part_feature(part, ACCELERATION_AVG_ABS + key_postfix)
                ] = part_features[ACCELERATION_AVG_ABS + key_postfix]
                features[
                    get_part_feature(part, ASCENDENT_AVERAGE + key_postfix)
                ] = part_features[ASCENDENT_AVERAGE + key_postfix]
                features[
                    get_part_feature(part, DESCENDENT_AVERAGE + key_postfix)
                ] = part_features[DESCENDENT_AVERAGE + key_postfix]
                features[
                    get_part_feature(part, ASCENDENT_PROPORTION + key_postfix)
                ] = part_features[ASCENDENT_PROPORTION + key_postfix]
                features[
                    get_part_feature(part, DESCENDENT_PROPORTION + key_postfix)
                ] = part_features[DESCENDENT_PROPORTION + key_postfix]

        part_prefix = get_part_prefix(part_data[DATA_PART_ABBREVIATION])
        intervals = part_data[DATA_INTERVALS]
        interval_features = get_interval_features(intervals, part_prefix)
        interval_count_features = get_interval_count_features(intervals, part_prefix)
        interval_type_features = get_interval_type_features(intervals, part_prefix)
        interval_stats_features = get_interval_stats_features(intervals, part_prefix)

        if all([i in features for i in interval_features.keys()]):
            _mix_data_with_precedent_data(features, interval_features)
        else:
            features.update(interval_features)
        if all([i in features for i in interval_count_features.keys()]):
            _mix_data_with_precedent_data(features, interval_count_features)
        else:
            features.update(interval_count_features)
        if all([i in features for i in interval_type_features.keys()]):
            _mix_data_with_precedent_data(features, interval_type_features)
        else:
            features.update(interval_type_features)
        if all([i in features for i in interval_stats_features.keys()]):
            _mix_data_with_precedent_data(features, interval_stats_features)
        else:
            features.update(interval_stats_features)

    parts_data_per_sound = {
        part_data[DATA_SOUND_ABBREVIATION]: [] for part_data in parts_data
    }
    for part_data in parts_data:
        sound = part_data[DATA_SOUND_ABBREVIATION]
        parts_data_per_sound[sound].append(part_data)

    for sound, sound_parts_data in parts_data_per_sound.items():
        sound_prefix = get_sound_prefix(sound)
        intervals = [
            interval
            for part_data in sound_parts_data
            for interval in part_data[DATA_INTERVALS]
        ]
        features.update(get_interval_features(intervals, sound_prefix))
        features.update(get_interval_count_features(intervals, sound_prefix))
        features.update(get_interval_type_features(intervals, sound_prefix))
        features.update(get_interval_stats_features(intervals, sound_prefix))

    score_intervals = [
        interval for part_data in parts_data for interval in part_data[DATA_INTERVALS]
    ]
    score_prefix = get_score_prefix()

    features.update(get_interval_features(score_intervals, score_prefix))
    features.update(get_interval_count_features(score_intervals, score_prefix))
    features.update(get_interval_type_features(score_intervals, score_prefix))
    features.update(get_interval_stats_features(score_intervals, score_prefix))

    score_features.update(features)


def get_interval_features(intervals: List[Interval], prefix: str = ""):
    numeric_intervals = [interval.semitones for interval in intervals]
    absolute_numeric_intervals = [
        abs(numeric_interval) for numeric_interval in numeric_intervals
    ]
    ascending_intervals = [
        numeric_interval
        for numeric_interval in numeric_intervals
        if numeric_interval > 0
    ]
    descending_intervals = [
        numeric_interval
        for numeric_interval in numeric_intervals
        if numeric_interval < 0
    ]

    absolute_intervallic_mean = (
        mean(absolute_numeric_intervals) if len(intervals) > 0 else 0
    )
    intervallic_mean = mean(numeric_intervals) if len(intervals) > 0 else 0
    ascending_intervallic_mean = (
        mean(ascending_intervals) if len(ascending_intervals) > 0 else 0
    )
    descending_intervallic_mean = (
        mean(descending_intervals) if len(descending_intervals) > 0 else 0
    )
    with np.errstate(invalid="ignore"):
        absolute_intervallic_std = (
            stdev(absolute_numeric_intervals) if len(intervals) > 1 else 0
        )
        intervallic_std = stdev(numeric_intervals) if len(intervals) > 1 else 0
        ascending_intervallic_std = (
            stdev(ascending_intervals) if len(ascending_intervals) > 1 else 0
        )
        descending_intervallic_std = (
            stdev(descending_intervals) if len(descending_intervals) > 1 else 0
        )
    mean_interval = Interval(int(round(absolute_intervallic_mean))).directedName

    cutoff = 0.1
    limits = (cutoff, cutoff)
    trimmed_intervallic_mean = (
        trimmed_mean(numeric_intervals, limits) if len(intervals) > 0 else 0
    )
    trimmed_absolute_intervallic_mean = (
        trimmed_mean(absolute_numeric_intervals, limits) if len(intervals) > 0 else 0
    )
    with np.errstate(invalid="ignore"):
        trimmed_intervallic_std = (
            trimmed_std(numeric_intervals, limits) if len(intervals) > 1 else 0
        )
        trimmed_absolute_intervallic_std = (
            trimmed_std(absolute_numeric_intervals, limits) if len(intervals) > 1 else 0
        )
    trim_diff = intervallic_mean - trimmed_intervallic_mean
    trim_ratio = trim_diff / intervallic_mean if intervallic_mean != 0 else 0
    absolute_trim_diff = absolute_intervallic_mean - trimmed_absolute_intervallic_mean
    absolute_trim_ratio = (
        absolute_trim_diff / absolute_intervallic_mean
        if absolute_intervallic_mean != 0
        else 0
    )
    num_ascending_intervals = (
        len(ascending_intervals) if len(ascending_intervals) > 0 else 0
    )
    num_descending_intervals = (
        len(descending_intervals) if len(descending_intervals) > 0 else 0
    )
    num_ascending_semitones = (
        sum(ascending_intervals) if len(ascending_intervals) > 0 else 0
    )
    num_descending_semitones = (
        sum(descending_intervals) if len(descending_intervals) > 0 else 0
    )
    ascending_intervals_percentage = (
        num_ascending_intervals / len(intervals) if len(intervals) > 0 else 0
    )
    descending_intervals_percentage = (
        num_descending_intervals / len(intervals) if len(intervals) > 0 else 0
    )

    largest_semitones = max(numeric_intervals) if len(numeric_intervals) > 0 else None
    largest = (
        Interval(largest_semitones).directedName if len(numeric_intervals) > 0 else None
    )
    smallest_semitones = (
        sorted(numeric_intervals, key=abs)[0] if len(numeric_intervals) > 0 else None
    )
    smallest = Interval(smallest_semitones).directedName if len(intervals) > 0 else None
    largest_ascending_semitones = (
        max(ascending_intervals) if len(ascending_intervals) > 0 else None
    )
    largest_ascending = (
        Interval(largest_ascending_semitones).directedName
        if len(ascending_intervals) > 0
        else None
    )
    largest_descending_semitones = (
        min(descending_intervals) if len(descending_intervals) > 0 else None
    )
    largest_descending = (
        Interval(largest_descending_semitones).directedName
        if len(descending_intervals) > 0
        else None
    )
    smallest_ascending_semitones = (
        min(ascending_intervals) if len(ascending_intervals) > 0 else None
    )
    smallest_ascending = (
        Interval(smallest_ascending_semitones).directedName
        if len(ascending_intervals) > 0
        else None
    )
    smallest_descending_semitones = (
        max(descending_intervals) if len(descending_intervals) > 0 else None
    )
    smallest_descending = (
        Interval(smallest_descending_semitones).directedName
        if len(descending_intervals) > 0
        else None
    )

    features = {
        f"{prefix}{MEAN_INTERVAL}": mean_interval,
        f"{prefix}{INTERVALLIC_MEAN}": intervallic_mean,
        f"{prefix}{INTERVALLIC_STD}": intervallic_std,
        f"{prefix}{ABSOLUTE_INTERVALLIC_MEAN}": absolute_intervallic_mean,
        f"{prefix}{ABSOLUTE_INTERVALLIC_STD}": absolute_intervallic_std,
        f"{prefix}{ASCENDING_INTERVALLIC_MEAN}": ascending_intervallic_mean,
        f"{prefix}{ASCENDING_INTERVALLIC_STD}": ascending_intervallic_std,
        f"{prefix}{DESCENDING_INTERVALLIC_MEAN}": descending_intervallic_mean,
        f"{prefix}{DESCENDING_INTERVALLIC_STD}": descending_intervallic_std,
        f"{prefix}{TRIMMED_INTERVALLIC_MEAN}": trimmed_intervallic_mean,
        f"{prefix}{TRIMMED_INTERVALLIC_STD}": trimmed_intervallic_std,
        f"{prefix}{TRIMMED_ABSOLUTE_INTERVALLIC_MEAN}": trimmed_absolute_intervallic_mean,
        f"{prefix}{TRIMMED_ABSOLUTE_INTERVALLIC_STD}": trimmed_absolute_intervallic_std,
        f"{prefix}{INTERVALLIC_TRIM_DIFF}": trim_diff,
        f"{prefix}{INTERVALLIC_TRIM_RATIO}": trim_ratio,
        f"{prefix}{ABSOLUTE_INTERVALLIC_TRIM_DIFF}": absolute_trim_diff,
        f"{prefix}{ABSOLUTE_INTERVALLIC_TRIM_RATIO}": absolute_trim_ratio,
        f"{prefix}{ASCENDING_INTERVALS_COUNT}": num_ascending_intervals,
        f"{prefix}{DESCENDING_INTERVALS_COUNT}": num_descending_intervals,
        f"{prefix}{ASCENDING_SEMITONES_SUM}": num_ascending_semitones,
        f"{prefix}{DESCENDING_SEMITONES_SUM}": num_descending_semitones,
        f"{prefix}{ASCENDING_INTERVALS_PER}": ascending_intervals_percentage,
        f"{prefix}{DESCENDING_INTERVALS_PER}": descending_intervals_percentage,
        f"{prefix}{LARGEST_INTERVAL_ALL}": largest,
        f"{prefix}{LARGEST_INTERVAL_ASC}": largest_ascending,
        f"{prefix}{LARGEST_INTERVAL_DESC}": largest_descending,
        f"{prefix}{LARGEST_SEMITONES_ALL}": largest_semitones,
        f"{prefix}{LARGEST_SEMITONES_ASC}": largest_ascending_semitones,
        f"{prefix}{LARGEST_SEMITONES_DESC}": largest_descending_semitones,
        f"{prefix}{LARGEST_ABSOLUTE_SEMITONES_ALL}": abs(largest_semitones)
        if largest_semitones is not None
        else None,
        f"{prefix}{LARGEST_ABSOLUTE_SEMITONES_ASC}": abs(largest_ascending_semitones)
        if largest_ascending_semitones is not None
        else None,
        f"{prefix}{LARGEST_ABSOLUTE_SEMITONES_DESC}": abs(largest_descending_semitones)
        if largest_descending_semitones is not None
        else None,
        f"{prefix}{SMALLEST_INTERVAL_ALL}": smallest,
        f"{prefix}{SMALLEST_INTERVAL_ASC}": smallest_ascending,
        f"{prefix}{SMALLEST_INTERVAL_DESC}": smallest_descending,
        f"{prefix}{SMALLEST_SEMITONES_ALL}": smallest_semitones,
        f"{prefix}{SMALLEST_SEMITONES_ASC}": smallest_ascending_semitones,
        f"{prefix}{SMALLEST_SEMITONES_DESC}": smallest_descending_semitones,
        f"{prefix}{SMALLEST_ABSOLUTE_SEMITONES_ALL}": abs(smallest_semitones)
        if smallest_semitones is not None
        else None,
        f"{prefix}{SMALLEST_ABSOLUTE_SEMITONES_ASC}": abs(smallest_ascending_semitones)
        if smallest_ascending_semitones is not None
        else None,
        f"{prefix}{SMALLEST_ABSOLUTE_SEMITONES_DESC}": abs(
            smallest_descending_semitones
        )
        if smallest_descending_semitones is not None
        else None,
    }
    return features


def get_interval_count_features(intervals: List[Interval], prefix: str = "") -> dict:
    interval_counts = Counter([interval.directedName for interval in intervals])
    total_count = len(intervals)
    interval_features = {}
    for interval, count in interval_counts.items():
        interval_features[
            INTERVAL_COUNT.format(prefix=prefix, interval=interval)
        ] = count
        interval_features[INTERVAL_PER.format(prefix=prefix, interval=interval)] = (
            count / total_count if total_count else 0
        )
    return interval_features


def get_interval_type_features(intervals_list: List[Interval], prefix: str = ""):
    repeated_notes_list = []
    stepwise_list = []
    leaps_list = []
    within_octave_list = []
    beyond_octave_list = []
    perfect_list = []
    major_list = []
    minor_list = []
    double_augmented_list = []
    augmented_list = []
    double_diminished_list = []
    diminished_list = []
    for interval in intervals_list:
        name = interval.directedName
        interval_number = int(extract_digits(name))
        if interval_number == 1:
            repeated_notes_list.append(interval)
        elif interval_number == 2:
            stepwise_list.append(interval)
        elif interval_number >= 3:
            leaps_list.append(interval)

        if abs(interval.semitones) <= 12:
            within_octave_list.append(interval)
        else:
            beyond_octave_list.append(interval)

        if name.startswith("AA"):
            double_augmented_list.append(interval)
        elif name.startswith("A"):
            augmented_list.append(interval)
        elif name.startswith("M"):
            major_list.append(interval)
        elif name.lower().startswith("p"):
            perfect_list.append(interval)
        elif name.startswith("m"):
            minor_list.append(interval)
        elif name.startswith("dd"):
            double_diminished_list.append(interval)
        elif name.startswith("d"):
            diminished_list.append(interval)
        else:
            raise ValueError(f"Unexpected interval name: {name}")
    all_intervals = len(intervals_list)
    all_repeated = len(repeated_notes_list)
    all_stepwise, ascending_stepwise, descending_stepwise = get_all_asc_desc_count(
        stepwise_list
    )
    all_leaps, ascending_leaps, descending_leaps = get_all_asc_desc_count(leaps_list)
    (
        all_within_octave,
        ascending_within_octave,
        descending_within_octave,
    ) = get_all_asc_desc_count(within_octave_list)
    (
        all_beyond_octave,
        ascending_beyond_octave,
        descending_beyond_octave,
    ) = get_all_asc_desc_count(beyond_octave_list)
    (
        all_double_augmented,
        ascending_double_augmented,
        descending_double_augmented,
    ) = get_all_asc_desc_count(double_augmented_list)
    all_augmented, ascending_augmented, descending_augmented = get_all_asc_desc_count(
        augmented_list
    )
    all_major, ascending_major, descending_major = get_all_asc_desc_count(major_list)
    all_perfect, ascending_perfect, descending_perfect = get_all_asc_desc_count(
        perfect_list
    )
    all_minor, ascending_minor, descending_minor = get_all_asc_desc_count(minor_list)
    (
        all_diminished,
        ascending_diminished,
        descending_diminished,
    ) = get_all_asc_desc_count(diminished_list)
    (
        all_double_diminished,
        ascending_double_diminished,
        descending_double_diminished,
    ) = get_all_asc_desc_count(double_diminished_list)

    return {
        f"{prefix}{REPEATED_NOTES_COUNT}": all_repeated,
        f"{prefix}{REPEATED_NOTES_PER}": all_repeated / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{STEPWISE_MOTION_ASC_COUNT}": ascending_stepwise,
        f"{prefix}{STEPWISE_MOTION_DESC_COUNT}": descending_stepwise,
        f"{prefix}{STEPWISE_MOTION_ALL_COUNT}": all_stepwise,
        f"{prefix}{STEPWISE_MOTION_ASC_PER}": ascending_stepwise / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{STEPWISE_MOTION_DESC_PER}": descending_stepwise / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{STEPWISE_MOTION_ALL_PER}": all_stepwise / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{LEAPS_ASC_COUNT}": ascending_leaps,
        f"{prefix}{LEAPS_DESC_COUNT}": descending_leaps,
        f"{prefix}{LEAPS_ALL_COUNT}": all_leaps,
        f"{prefix}{LEAPS_ASC_PER}": ascending_leaps / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{LEAPS_DESC_PER}": descending_leaps / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{LEAPS_ALL_PER}": all_leaps / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_PERFECT_ASC_COUNT}": ascending_perfect,
        f"{prefix}{INTERVALS_PERFECT_DESC_COUNT}": descending_perfect,
        f"{prefix}{INTERVALS_PERFECT_ALL_COUNT}": all_perfect,
        f"{prefix}{INTERVALS_PERFECT_ASC_PER}": ascending_perfect / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_PERFECT_DESC_PER}": descending_perfect / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_PERFECT_ALL_PER}": all_perfect / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_MAJOR_ASC_COUNT}": ascending_major,
        f"{prefix}{INTERVALS_MAJOR_DESC_COUNT}": descending_major,
        f"{prefix}{INTERVALS_MAJOR_ALL_COUNT}": all_major,
        f"{prefix}{INTERVALS_MAJOR_ASC_PER}": ascending_major / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_MAJOR_DESC_PER}": descending_major / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_MAJOR_ALL_PER}": all_major / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_MINOR_ASC_COUNT}": ascending_minor,
        f"{prefix}{INTERVALS_MINOR_DESC_COUNT}": descending_minor,
        f"{prefix}{INTERVALS_MINOR_ALL_COUNT}": all_minor,
        f"{prefix}{INTERVALS_MINOR_ASC_PER}": ascending_minor / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_MINOR_DESC_PER}": descending_minor / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_MINOR_ALL_PER}": all_minor / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_AUGMENTED_ASC_COUNT}": ascending_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_DESC_COUNT}": descending_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_ALL_COUNT}": all_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_ASC_PER}": ascending_augmented / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_AUGMENTED_DESC_PER}": descending_augmented / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_AUGMENTED_ALL_PER}": all_augmented / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_DIMINISHED_ASC_COUNT}": ascending_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_DESC_COUNT}": descending_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_ALL_COUNT}": all_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_ASC_PER}": ascending_diminished / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_DIMINISHED_DESC_PER}": descending_diminished
        / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_DIMINISHED_ALL_PER}": all_diminished / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ASC_COUNT}": ascending_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_DESC_COUNT}": descending_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ALL_COUNT}": all_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ASC_PER}": ascending_double_augmented
        / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_DESC_PER}": descending_double_augmented
        / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ALL_PER}": all_double_augmented
        / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ASC_COUNT}": ascending_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_DESC_COUNT}": descending_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ALL_COUNT}": all_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ASC_PER}": ascending_double_diminished
        / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_DESC_PER}": descending_double_diminished
        / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ALL_PER}": all_double_diminished
        / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ASC_COUNT}": ascending_within_octave,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_DESC_COUNT}": descending_within_octave,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ALL_COUNT}": all_within_octave,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ASC_PER}": ascending_within_octave
        / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_DESC_PER}": descending_within_octave
        / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ALL_PER}": all_within_octave / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ASC_COUNT}": ascending_beyond_octave,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_DESC_COUNT}": descending_beyond_octave,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ALL_COUNT}": all_beyond_octave,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ASC_PER}": ascending_beyond_octave
        / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_DESC_PER}": descending_beyond_octave
        / all_intervals
        if all_intervals != 0
        else 0,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ALL_PER}": all_beyond_octave / all_intervals
        if all_intervals != 0
        else 0,
    }


def get_ascending_descending(
    intervals: List[Interval],
) -> Tuple[List[Interval], List[Interval]]:
    ascending = [interval for interval in intervals if interval.semitones > 0]
    descending = [interval for interval in intervals if interval.semitones < 0]
    return ascending, descending


def get_all_asc_desc_count(intervals: List[Interval]) -> Tuple[int, int, int]:
    ascending, descending = get_ascending_descending(intervals)
    return len(intervals), len(ascending), len(descending)


def get_interval_stats_features(intervals: List[Interval], prefix: str = ""):
    numeric_intervals = np.array([interval.semitones for interval in intervals])
    absolute_numeric_intervals = abs(numeric_intervals)
    with np.errstate(invalid="ignore"):
        intervals_skewness = (
            skew(numeric_intervals, bias=False)
            if [i for i in numeric_intervals if i != 0]
            else None
        )
        intervals_kurtosis = (
            kurtosis(numeric_intervals, bias=False)
            if [i for i in numeric_intervals if i != 0]
            else None
        )
        absolute_intervals_skewness = (
            skew(absolute_numeric_intervals, bias=False)
            if [i for i in absolute_numeric_intervals if i != 0]
            else None
        )
        absolute_intervals_kurtosis = (
            kurtosis(absolute_numeric_intervals, bias=False)
            if [i for i in absolute_numeric_intervals if i != 0]
            else None
        )

    return {
        f"{prefix}{INTERVALLIC_SKEWNESS}": intervals_skewness,
        f"{prefix}{INTERVALLIC_KURTOSIS}": intervals_kurtosis,
        f"{prefix}{ABSOLUTE_INTERVALLIC_SKEWNESS}": absolute_intervals_skewness,
        f"{prefix}{ABSOLUTE_INTERVALLIC_KURTOSIS}": absolute_intervals_kurtosis,
    }


def _motion_postfix(step, win):
    key_postfix = f"_step_{step}_win_{win}"
    return key_postfix


def _motion_features_single_window_step(
    notes_duration: List[float], notes_midi: List[int], step: float, win: int
) -> Dict[str, Union[float, np.ndarray]]:
    """
    Calculates motion features for a single window step of an aria.

    Parameters:
    notes_duration (List[float]): List of note durations in seconds.
    notes_midi (List[int]): List of MIDI note numbers.
    step (float): Step size in seconds.
    win (int): Window size in compasses.

    Returns:
    Dict[str, Union[float, np.ndarray]]: Dictionary containing the following motion features:
        - SPEED_AVG_ABS_{step}_{win} Average absolute speed.
        - ACCELERATION_AVG_ABS_{step}_{win} Average absolute acceleration.
        - ASCENDENT_AVERAGE_{step}_{win} Average length of prolonged ascent chunks in the smoothed midis of the aria.
        - DESCENDENT_AVERAGE_{step}_{win} Average length of prolonged descent chunks in the smoothed midis of the aria.
        - ASCENDENT_PROPORTION_{step}_{win} Proportion of prolonged ascent chunks over the total of the aria.
        - DESCENDENT_PROPORTION_{step}_{win} Proportion of prolonged descent chunks over the total of the aria.
    """
    key_postfix = _motion_postfix(step, win)
    default_dict = {
        SPEED_AVG_ABS + key_postfix: 0,
        ACCELERATION_AVG_ABS + key_postfix: 0,
        ASCENDENT_AVERAGE + key_postfix: 0,
        DESCENDENT_AVERAGE + key_postfix: 0,
        ASCENDENT_PROPORTION + key_postfix: 0,
        DESCENDENT_PROPORTION + key_postfix: 0,
    }
    
    if len(notes_midi) == 0:
        return default_dict
    midis_raw = np.repeat(notes_midi, np.divide(notes_duration, step).astype(int), axis=0)
    if midis_raw.size == 0:
        return default_dict

    # Absolute means of speed and acceleration
    spe_raw = np.diff(midis_raw) / step
    if spe_raw.size > 0:
        spe_avg_abs = np.mean(abs(spe_raw))
    else:
        spe_avg_abs = 0
    acc_raw = np.diff(spe_raw) / step
    if acc_raw.size > 0:
        acc_avg_abs = np.mean(abs(acc_raw))
    else:
        acc_avg_abs = 0

    # Rolling mean to smooth the midis by +-1 compasses -- not required for
    # statistics based on means but important for detecting increasing sequences
    # with a tolerance.
    midis_smo_series = pd.Series(midis_raw)
    midis_smo = [
        np.mean(i.to_list()) for i in midis_smo_series.rolling(2 * win + 1, center=True)
    ]

    # Prolonged ascent/descent chunks in smoothed midis of the aria (allows for
    # small violations in the form of decrements/increments that do not
    # decrease/increase the rolling mean).
    dife = np.diff(midis_smo)

    asc = [(k, sum(1 for i in g)) for k, g in groupby(dife > 0)]
    dsc = [(k, sum(1 for i in g)) for k, g in groupby(dife < 0)]

    asc = [i for b, i in asc if b]
    dsc = [i for b, i in dsc if b]

    # Average length of ascent/descent chunks of the aria
    asc_avg = mean(asc) if asc else 0 #np.nan
    dsc_avg = mean(dsc) if dsc else 0 #np.nan

    # Proportion of ascent/descent chunks over the total of the aria
    asc_prp = sum(asc) / (len(dife) - 1) if asc else 0 #np.nan
    dsc_prp = sum(dsc) / (len(dife) - 1) if dsc else 0 #np.nan

    return {
        SPEED_AVG_ABS + key_postfix: spe_avg_abs,
        ACCELERATION_AVG_ABS + key_postfix: acc_avg_abs,
        ASCENDENT_AVERAGE + key_postfix: asc_avg,
        DESCENDENT_AVERAGE + key_postfix: dsc_avg,
        ASCENDENT_PROPORTION + key_postfix: asc_prp,
        DESCENDENT_PROPORTION + key_postfix: dsc_prp,
    }


def get_motion_features(part_data) -> dict:
    """
    Extracts motion features from the given part data.

    Parameters:
    part_data (dict): A dictionary containing the notes and rests of a music part.

    Returns:
    dict: A dictionary containing the extracted motion features.

    Raises:
    This function does not raise any exceptions.
    """
    notes_midi = []
    notes_duration = []
    for note in part_data["notes_and_rests"]:
        if hasattr(note, "pitch"):
            notes_midi.append(note.pitch.midi)
            notes_duration.append(note.duration.quarterLength)

    notes_midi = np.asarray(notes_midi)
    notes_duration = np.asarray(notes_duration)

    return_dict = {}
    for step in MOTION_STEPS:
        for win in MOTION_WINS:
            return_dict.update(
                _motion_features_single_window_step(
                    notes_duration, notes_midi, step, win
                )
            )
    return return_dict
