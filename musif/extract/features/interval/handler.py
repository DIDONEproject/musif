from collections import Counter
from statistics import mean, stdev
from typing import Dict, List, Tuple

import numpy as np
from music21.interval import Interval
from scipy.stats import kurtosis, skew

from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.constants import DATA_PART_ABBREVIATION
from musif.extract.features.core.constants import DATA_NUMERIC_INTERVALS, DATA_TEXT_INTERVALS
from musif.extract.features.prefix import get_part_prefix, get_score_prefix
from .constants import *


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    numeric_intervals = part_data[DATA_NUMERIC_INTERVALS]
    text_intervals = part_data[DATA_TEXT_INTERVALS]
    text_intervals_count = Counter(text_intervals)

    part_features.update(get_interval_features(numeric_intervals))
    part_features.update(get_interval_count_features(text_intervals_count))
    part_features.update(get_interval_type_features(text_intervals_count))
    part_features.update(get_interval_stats_features(text_intervals_count))


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    parts_data = filter_parts_data(parts_data, cfg.parts_filter)
    if len(parts_data) == 0:
        return

    features = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part_prefix = get_part_prefix(part_data[DATA_PART_ABBREVIATION])
        numeric_intervals = [interval for part_data in parts_data for interval in part_data[DATA_NUMERIC_INTERVALS]]
        text_intervals = [interval for part_data in parts_data for interval in part_data[DATA_TEXT_INTERVALS]]
        text_intervals_count = Counter(text_intervals)
        features.update(get_interval_features(numeric_intervals, part_prefix))
        features.update(get_interval_count_features(text_intervals_count, part_prefix))
        features.update(get_interval_type_features(text_intervals_count, part_prefix))
        features.update(get_interval_stats_features(text_intervals_count, part_prefix))
        for feature_name in SCORE_FEATURES:
            features[f"{part_prefix}{feature_name}"] = part_features[feature_name]

    numeric_intervals = [interval for part_data in parts_data for interval in part_data[DATA_NUMERIC_INTERVALS]]
    text_intervals = [interval for part_data in parts_data for interval in part_data[DATA_TEXT_INTERVALS]]
    text_intervals_count = Counter(text_intervals)
    score_prefix = get_score_prefix()
    features.update(get_interval_features(numeric_intervals, score_prefix))
    features.update(get_interval_count_features(text_intervals_count, score_prefix))
    features.update(get_interval_type_features(text_intervals_count, score_prefix))
    features.update(get_interval_stats_features(text_intervals_count, score_prefix))
    score_features.update(features)


def get_interval_features(numeric_intervals: List[int], prefix: str = ""):
    numeric_intervals = sorted(numeric_intervals)
    absolute_numeric_intervals = sorted([abs(interval) for interval in numeric_intervals])
    ascending_intervals = [interval for interval in numeric_intervals if interval > 0]
    descending_intervals = [interval for interval in numeric_intervals if interval < 0]
    absolute_intervallic_mean = mean(absolute_numeric_intervals) if len(absolute_numeric_intervals) > 0 else 0
    absolute_intervallic_std = stdev(absolute_numeric_intervals) if len(absolute_numeric_intervals) > 1 else 0
    absolute_descending_numeric_intervals = sorted([abs(interval) for interval in numeric_intervals if interval < 0])
    intervallic_mean = mean(numeric_intervals) if len(numeric_intervals) > 0 else 0
    intervallic_std = stdev(numeric_intervals) if len(numeric_intervals) > 1 else 0
    ascending_intervallic_mean = mean(ascending_intervals) if len(ascending_intervals) > 0 else 0
    ascending_intervallic_std = stdev(ascending_intervals) if len(ascending_intervals) > 1 else 0
    descending_intervallic_mean = mean(descending_intervals) if len(descending_intervals) > 0 else 0
    descending_intervallic_std = stdev(descending_intervals) if len(descending_intervals) > 1 else 0
    absolute_descending_intervallic_mean = mean(absolute_descending_numeric_intervals) if len(absolute_descending_numeric_intervals) > 0 else 0
    absolute_descending_intervallic_std = stdev(absolute_descending_numeric_intervals) if len(absolute_descending_numeric_intervals) > 1 else 0
    mean_interval = Interval(int(round(absolute_intervallic_mean))).directedName

    cutoff = 0.1
    cutoff_elements = int(cutoff * len(numeric_intervals))
    trimmed_intervals = numeric_intervals[cutoff_elements:len(numeric_intervals) - cutoff_elements] if len(numeric_intervals) > 0 else []
    trimmed_intervallic_mean = mean(trimmed_intervals) if len(trimmed_intervals) > 0 else 0
    trimmed_intervallic_std = stdev(trimmed_intervals) if len(trimmed_intervals) > 1 else 0
    trimmed_absolute_intervals = absolute_numeric_intervals[cutoff_elements:len(numeric_intervals) - cutoff_elements] if len(absolute_numeric_intervals) > 0 else []
    trimmed_absolute_intervallic_mean = mean(trimmed_absolute_intervals) if len(trimmed_absolute_intervals) > 0 else 0
    trimmed_absolute_intervallic_std = stdev(trimmed_absolute_intervals) if len(trimmed_absolute_intervals) > 1 else 0
    trim_diff = intervallic_mean - trimmed_intervallic_mean
    trim_ratio = trim_diff / intervallic_mean if intervallic_mean != 0 else 0
    absolute_trim_diff = absolute_intervallic_mean - trimmed_absolute_intervallic_mean
    absolute_trim_ratio = absolute_trim_diff / absolute_intervallic_mean if absolute_intervallic_mean != 0 else 0
    num_ascending_intervals = len(ascending_intervals) if len(ascending_intervals) > 0 else 0
    num_descending_intervals = len(descending_intervals) if len(descending_intervals) > 0 else 0
    num_ascending_semitones = sum(ascending_intervals) if len(ascending_intervals) > 0 else 0
    num_descending_semitones = sum(descending_intervals) if len(descending_intervals) > 0 else 0
    ascending_intervals_percentage = num_ascending_intervals / len(numeric_intervals) if len(numeric_intervals) > 0 else 0
    descending_intervals_percentage = num_descending_intervals / len(numeric_intervals) if len(numeric_intervals) > 0 else 0

    ascending_intervals = [interval for interval in numeric_intervals if interval > 0]
    descending_intervals = [interval for interval in numeric_intervals if interval < 0]
    largest_semitones = max(numeric_intervals) if len(numeric_intervals) > 0 else None
    largest = Interval(largest_semitones).directedName if len(numeric_intervals) > 0 else None
    smallest_semitones = sorted(numeric_intervals, key=abs)[0] if len(numeric_intervals) > 0 else None
    smallest = Interval(smallest_semitones).directedName if len(numeric_intervals) > 0 else None
    largest_ascending_semitones = max(ascending_intervals) if len(ascending_intervals) > 0 else None
    largest_ascending = Interval(largest_ascending_semitones).directedName if len(ascending_intervals) > 0 else None
    largest_descending_semitones = min(descending_intervals) if len(descending_intervals) > 0 else None
    largest_descending = Interval(largest_descending_semitones).directedName if len(descending_intervals) > 0 else None
    smallest_ascending_semitones = min(ascending_intervals) if len(ascending_intervals) > 0 else None
    smallest_ascending = Interval(smallest_ascending_semitones).directedName if len(ascending_intervals) > 0 else None
    smallest_descending_semitones = max(descending_intervals) if len(descending_intervals) > 0 else None
    smallest_descending = Interval(smallest_descending_semitones).directedName if len(descending_intervals) > 0 else None

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
        f"{prefix}{ABSOLUTE_DESCENDING_INTERVALLIC_MEAN}": absolute_descending_intervallic_mean,
        f"{prefix}{ABSOLUTE_DESCENDING_INTERVALLIC_STD}": absolute_descending_intervallic_std,
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
        f"{prefix}{LARGEST_ABSOLUTE_SEMITONES_ALL}": abs(largest_semitones) if largest_semitones else None,
        f"{prefix}{LARGEST_ABSOLUTE_SEMITONES_ASC}": abs(largest_ascending_semitones) if largest_ascending_semitones else None,
        f"{prefix}{LARGEST_ABSOLUTE_SEMITONES_DESC}": abs(largest_descending_semitones) if largest_descending_semitones else None,
        f"{prefix}{SMALLEST_INTERVAL_ALL}": smallest,
        f"{prefix}{SMALLEST_INTERVAL_ASC}": smallest_ascending,
        f"{prefix}{SMALLEST_INTERVAL_DESC}": smallest_descending,
        f"{prefix}{SMALLEST_SEMITONES_ALL}": smallest_semitones,
        f"{prefix}{SMALLEST_SEMITONES_ASC}": smallest_ascending_semitones,
        f"{prefix}{SMALLEST_SEMITONES_DESC}": smallest_descending_semitones,
        f"{prefix}{SMALLEST_ABSOLUTE_SEMITONES_ALL}": abs(smallest_semitones) if smallest_semitones else None,
        f"{prefix}{SMALLEST_ABSOLUTE_SEMITONES_ASC}": abs(smallest_ascending_semitones) if smallest_ascending_semitones else None,
        f"{prefix}{SMALLEST_ABSOLUTE_SEMITONES_DESC}": abs(smallest_descending_semitones) if smallest_descending_semitones else None,
    }
    return features


def get_interval_count_features(interval_counts: Dict[str, int], prefix: str = "") -> dict:
    total_count = sum([count for interval, count in interval_counts.items()])
    interval_features = {}
    for interval, count in interval_counts.items():
        interval_features[INTERVAL_COUNT.format(prefix=prefix, interval=interval)] = count
        interval_features[INTERVAL_PER.format(prefix=prefix, interval=interval)] = count / total_count
    return interval_features


def get_interval_type_features(intervals_count: Dict[str, int], prefix: str = ""):
    """
    Function needed for generating IIIIntervals_types. It applies computations to the input dictionary
    The 'intervals' dictionary contains as key the interval name, and as value its frequency.

    """
    intervals_names = list(intervals_count.keys())

    # repeated notes (addition of P1, P-1)
    no_semitones = {'P1', 'P-1', 'd2', 'd-2'}
    no_semitones_data = sum([intervals_count.get(name, 0) for name in no_semitones])

    leaps = []
    stepwise = []
    within_octave = []
    beyond_octave = []
    perfect = []
    major = []
    minor = []
    double_augmented = []
    augmented = []
    double_diminished = []
    diminished = []
    all_intervals = 0
    for iname in intervals_names:
        if 1 <= abs(Interval(iname).semitones) <= 2:
            stepwise.append(iname)
        elif abs(Interval(iname).semitones) >= 3:
            leaps.append(iname)

        if abs(Interval(iname).semitones) <= 12:
            within_octave.append(iname)
        else:
            beyond_octave.append(iname)

        if iname.startswith('AA'):
            double_augmented.append(iname)
        elif iname.startswith("A"):
            augmented.append(iname)
        elif iname.startswith("M"):
            major.append(iname)
        elif iname.lower().startswith("p"):
            perfect.append(iname)
        elif iname.startswith("m"):
            minor.append(iname)
        elif iname.startswith("dd"):
            double_diminished.append(iname)
        elif iname.startswith("d"):
            diminished.append(iname)
        else:
            raise ValueError(f"Unexpected interval name: {iname}")
        all_intervals += intervals_count[iname]
    ascending_leaps, descending_leaps = get_ascending_descending(intervals_count, leaps)
    ascending_stepwise, descending_stepwise = get_ascending_descending(intervals_count, stepwise)
    ascending_double_augmented, descending_double_augmented = get_ascending_descending(intervals_count, double_augmented)
    ascending_augmented, descending_augmented = get_ascending_descending(intervals_count, augmented)
    ascending_major, descending_major = get_ascending_descending(intervals_count, major)
    ascending_perfect, descending_perfect = get_ascending_descending(intervals_count, perfect)
    ascending_minor, descending_minor = get_ascending_descending(intervals_count, minor)
    ascending_double_diminished, descending_double_diminished = get_ascending_descending(intervals_count, double_diminished)
    ascending_diminished, descending_diminished = get_ascending_descending(intervals_count, diminished)
    ascending_within_octave, descending_within_octave = get_ascending_descending(intervals_count, within_octave)
    ascending_beyond_octave, descending_beyond_octave = get_ascending_descending(intervals_count, beyond_octave)

    return {
        f"{prefix}{REPEATED_NOTES_COUNT}": no_semitones_data,
        f"{prefix}{REPEATED_NOTES_PER}": no_semitones_data / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{LEAPS_ASC_COUNT}": ascending_leaps,
        f"{prefix}{LEAPS_DESC_COUNT}": descending_leaps,
        f"{prefix}{LEAPS_ALL_COUNT}": ascending_leaps + descending_leaps,
        f"{prefix}{LEAPS_ASC_PER}": ascending_leaps / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{LEAPS_DESC_PER}": descending_leaps / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{LEAPS_ALL_PER}": (ascending_leaps + descending_leaps) / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{STEPWISE_MOTION_ASC_COUNT}": ascending_stepwise,
        f"{prefix}{STEPWISE_MOTION_DESC_COUNT}": descending_stepwise,
        f"{prefix}{STEPWISE_MOTION_ALL_COUNT}": ascending_stepwise + descending_stepwise,
        f"{prefix}{STEPWISE_MOTION_ASC_PER}": ascending_stepwise / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{STEPWISE_MOTION_DESC_PER}": descending_stepwise / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{STEPWISE_MOTION_ALL_PER}": (ascending_stepwise + descending_stepwise) / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_PERFECT_ASC_COUNT}": ascending_perfect,
        f"{prefix}{INTERVALS_PERFECT_DESC_COUNT}": descending_perfect,
        f"{prefix}{INTERVALS_PERFECT_ALL_COUNT}": ascending_perfect + descending_perfect,
        f"{prefix}{INTERVALS_PERFECT_ASC_PER}": ascending_perfect / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_PERFECT_DESC_PER}": descending_perfect / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_PERFECT_ALL_PER}": (ascending_perfect + descending_perfect) / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_MAJOR_ASC_COUNT}": ascending_major,
        f"{prefix}{INTERVALS_MAJOR_DESC_COUNT}": descending_major,
        f"{prefix}{INTERVALS_MAJOR_ALL_COUNT}": ascending_major + descending_major,
        f"{prefix}{INTERVALS_MAJOR_ASC_PER}": ascending_major / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_MAJOR_DESC_PER}": descending_major / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_MAJOR_ALL_PER}": (ascending_major + descending_major) / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_MINOR_ASC_COUNT}": ascending_minor,
        f"{prefix}{INTERVALS_MINOR_DESC_COUNT}": descending_minor,
        f"{prefix}{INTERVALS_MINOR_ALL_COUNT}": ascending_minor + descending_minor,
        f"{prefix}{INTERVALS_MINOR_ASC_PER}": ascending_minor / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_MINOR_DESC_PER}": descending_minor / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_MINOR_ALL_PER}": (ascending_minor + descending_minor) / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_AUGMENTED_ASC_COUNT}": ascending_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_DESC_COUNT}": descending_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_ALL_COUNT}": ascending_augmented + descending_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_ASC_PER}": ascending_augmented / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_AUGMENTED_DESC_PER}": descending_augmented / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_AUGMENTED_ALL_PER}": (ascending_augmented + descending_augmented) / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_DIMINISHED_ASC_COUNT}": ascending_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_DESC_COUNT}": descending_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_ALL_COUNT}": ascending_diminished + descending_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_ASC_PER}": ascending_diminished / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_DIMINISHED_DESC_PER}": descending_diminished / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_DIMINISHED_ALL_PER}": (ascending_diminished + descending_diminished) / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ASC_COUNT}": ascending_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_DESC_COUNT}": descending_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ALL_COUNT}": ascending_double_augmented + descending_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ASC_PER}": ascending_double_augmented / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_DESC_PER}": descending_double_augmented / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ALL_PER}": (ascending_double_augmented + descending_double_augmented) / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ASC_COUNT}": ascending_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_DESC_COUNT}": descending_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ALL_COUNT}": ascending_double_diminished + descending_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ASC_PER}": ascending_double_diminished / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_DESC_PER}": descending_double_diminished / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ALL_PER}": (ascending_double_diminished + descending_double_diminished) / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ASC_COUNT}": ascending_within_octave,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_DESC_COUNT}": descending_within_octave,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ALL_COUNT}": ascending_within_octave + descending_within_octave,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ASC_PER}": ascending_within_octave / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_DESC_PER}": descending_within_octave / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ALL_PER}": (ascending_within_octave + descending_within_octave) / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ASC_COUNT}": ascending_beyond_octave,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_DESC_COUNT}": descending_beyond_octave,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ALL_COUNT}": ascending_beyond_octave + descending_beyond_octave,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ASC_PER}": ascending_beyond_octave / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_DESC_PER}": descending_beyond_octave / all_intervals if all_intervals != 0 else 0,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ALL_PER}": (ascending_beyond_octave + descending_beyond_octave) / all_intervals if all_intervals != 0 else 0,
    }


def get_ascending_descending(intervals_count: Dict[str, int], names: List[str]) -> Tuple[int, int]:
    ascending_data = sum([intervals_count.get(name, 0) for name in names if '-' not in name])
    descending_data = sum([intervals_count.get(name, 0) for name in names if '-' in name])
    return ascending_data, descending_data


def get_interval_stats_features(intervals_count: Dict[str, int], prefix: str = ""):
    intervals = []
    absolute_intervals = []
    for interval, frequency in intervals_count.items():
        interval_semitones = Interval(interval).semitones
        absolute_interval_semitones = abs(interval_semitones)
        for i in range(frequency):
            intervals.append(interval_semitones)
            absolute_intervals.append(absolute_interval_semitones)
    intervals = np.array(intervals)
    absolute_intervals = np.array(absolute_intervals)
    intervals_skewness = skew(intervals)
    intervals_kurtosis = kurtosis(intervals)
    absolute_intervals_skewness = skew(absolute_intervals)
    absolute_intervals_kurtosis = kurtosis(absolute_intervals)
    return {
        f"{prefix}{INTERVALLIC_SKEWNESS}": intervals_skewness,
        f"{prefix}{INTERVALLIC_KURTOSIS}": intervals_kurtosis,
        f"{prefix}{ABSOLUTE_INTERVALLIC_SKEWNESS}": absolute_intervals_skewness,
        f"{prefix}{ABSOLUTE_INTERVALLIC_KURTOSIS}": absolute_intervals_kurtosis,
    }
