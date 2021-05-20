from collections import Counter
from statistics import mean, stdev
from typing import Dict, List, Tuple

import numpy as np
from music21.interval import Interval
from scipy.stats import kurtosis, skew

from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.features.prefix import get_corpus_prefix, get_part_prefix, get_score_prefix, get_sound_prefix

INTERVALLIC_MEAN = "IntervallicMean"
INTERVALLIC_STD = "IntervallicStd"
ABSOLUTE_INTERVALLIC_MEAN = "AbsoluteIntervallicMean"
ABSOLUTE_INTERVALLIC_STD = "AbsoluteIntervallicStd"
TRIMMED_INTERVALLIC_MEAN = "TrimmedIntervallicMean"
TRIMMED_INTERVALLIC_STD = "TrimmedIntervallicStd"
TRIMMED_ABSOLUTE_INTERVALLIC_MEAN = "TrimmedAbsoluteIntervallicMean"
TRIMMED_ABSOLUTE_INTERVALLIC_STD = "TrimmedAbsoluteIntervallicStd"
INTERVALLIC_TRIM_DIFF = "IntervallicTrimDiff"
INTERVALLIC_TRIM_RATIO = "IntervallicTrimRatio"
ABSOLUTE_INTERVALLIC_TRIM_DIFF = "AbsoluteIntervallicTrimDiff"
ABSOLUTE_INTERVALLIC_TRIM_RATIO = "AbsoluteIntervallicTrimRatio"
ASCENDING_SEMITONES = "AscendingSemitones"
DESCENDING_SEMITONES = "DescendingSemitones"
ASCENDING_INTERVALS_COUNT = "AscendingIntervals_Count"
ASCENDING_INTERVALS_PER = "AscendingIntervals_Per"
DESCENDING_INTERVALS_COUNT = "DescendingIntervals_Count"
DESCENDING_INTERVALS_PER = "DescendingIntervals_Per"
REPEATED_NOTES_COUNT = "RepeatedNotes_Count"
REPEATED_NOTES_PER = "RepeatedNotes_Per"
LEAPS_ASC_COUNT = "LeapsAsc_Count"
LEAPS_ASC_PER = "LeapsAsc_Per"
LEAPS_DESC_COUNT = "LeapsDesc_Count"
LEAPS_DESC_PER = "LeapsDesc_Per"
LEAPS_ALL_COUNT = "LeapsAll_Count"
LEAPS_ALL_PER = "LeapsAll_Per"
STEPWISE_MOTION_ASC_COUNT = "StepwiseMotionAsc_Count"
STEPWISE_MOTION_DESC_COUNT = "StepwiseMotionDesc_Count"
STEPWISE_MOTION_ALL_COUNT = "StepwiseMotionAll_Count"
STEPWISE_MOTION_ASC_PER = "StepwiseMotionAsc_Per"
STEPWISE_MOTION_DESC_PER = "StepwiseMotionDesc_Per"
STEPWISE_MOTION_ALL_PER = "StepwiseMotionAll_Per"
INTERVALS_PERFECT_ASC_COUNT = "IntervalsPerfectAsc_Count"
INTERVALS_PERFECT_DESC_COUNT = "IntervalsPerfectDesc_Count"
INTERVALS_PERFECT_ALL_COUNT = "IntervalsPerfectAll_Count"
INTERVALS_PERFECT_ASC_PER = "IntervalsPerfectAsc_Per"
INTERVALS_PERFECT_DESC_PER = "IntervalsPerfectDesc_Per"
INTERVALS_PERFECT_ALL_PER = "IntervalsPerfectAll_Per"
INTERVALS_MAJOR_ASC_COUNT = "IntervalsMajorAsc_Count"
INTERVALS_MAJOR_DESC_COUNT = "IntervalsMajorDesc_Count"
INTERVALS_MAJOR_ALL_COUNT = "IntervalsMajorAll_Count"
INTERVALS_MAJOR_ASC_PER = "IntervalsMajorAsc_Per"
INTERVALS_MAJOR_DESC_PER = "IntervalsMajorDesc_Per"
INTERVALS_MAJOR_ALL_PER = "IntervalsMajorAll_Per"
INTERVALS_MINOR_ASC_COUNT = "IntervalsMinorAsc_Count"
INTERVALS_MINOR_DESC_COUNT = "IntervalsMinorDesc_Count"
INTERVALS_MINOR_ALL_COUNT = "IntervalsMinorAll_Count"
INTERVALS_MINOR_ASC_PER = "IntervalsMinorAsc_Per"
INTERVALS_MINOR_DESC_PER = "IntervalsMinorDesc_Per"
INTERVALS_MINOR_ALL_PER = "IntervalsMinorAll_Per"
INTERVALS_AUGMENTED_ASC_COUNT = "IntervalsAugmentedAsc_Count"
INTERVALS_AUGMENTED_DESC_COUNT = "IntervalsAugmentedDesc_Count"
INTERVALS_AUGMENTED_ALL_COUNT = "IntervalsAugmentedAll_Count"
INTERVALS_AUGMENTED_ASC_PER = "IntervalsAugmentedAsc_Per"
INTERVALS_AUGMENTED_DESC_PER = "IntervalsAugmentedDesc_Per"
INTERVALS_AUGMENTED_ALL_PER = "IntervalsAugmentedAll_Per"
INTERVALS_DIMINISHED_ASC_COUNT = "IntervalsDiminishedAsc_Count"
INTERVALS_DIMINISHED_DESC_COUNT = "IntervalsDiminishedDesc_Count"
INTERVALS_DIMINISHED_ALL_COUNT = "IntervalsDiminishedAll_Count"
INTERVALS_DIMINISHED_ASC_PER = "IntervalsDiminishedAsc_Per"
INTERVALS_DIMINISHED_DESC_PER = "IntervalsDiminishedDesc_Per"
INTERVALS_DIMINISHED_ALL_PER = "IntervalsDiminishedAll_Per"
INTERVALS_DOUBLE_AUGMENTED_ASC_COUNT = "IntervalsDoubleAugmentedAsc_Count"
INTERVALS_DOUBLE_AUGMENTED_DESC_COUNT = "IntervalsDoubleAugmentedDesc_Count"
INTERVALS_DOUBLE_AUGMENTED_ALL_COUNT = "IntervalsDoubleAugmentedAll_Count"
INTERVALS_DOUBLE_AUGMENTED_ASC_PER = "IntervalsDoubleAugmentedAsc_Per"
INTERVALS_DOUBLE_AUGMENTED_DESC_PER = "IntervalsDoubleAugmentedDesc_Per"
INTERVALS_DOUBLE_AUGMENTED_ALL_PER = "IntervalsDoubleAugmentedAll_Per"
INTERVALS_DOUBLE_DIMINISHED_ASC_COUNT = "IntervalsDoubleDiminishedAsc_Count"
INTERVALS_DOUBLE_DIMINISHED_DESC_COUNT = "IntervalsDoubleDiminishedDesc_Count"
INTERVALS_DOUBLE_DIMINISHED_ALL_COUNT = "IntervalsDoubleDiminishedAll_Count"
INTERVALS_DOUBLE_DIMINISHED_ASC_PER = "IntervalsDoubleDiminishedAsc_Per"
INTERVALS_DOUBLE_DIMINISHED_DESC_PER = "IntervalsDoubleDiminishedDesc_Per"
INTERVALS_DOUBLE_DIMINISHED_ALL_PER = "IntervalsDoubleDiminishedAll_Per"
INTERVALS_SKEWNESS = "IntervalsSkewness"
INTERVALS_KURTOSIS = "IntervalsKurtosis"
LARGEST_ASC_INTERVAL = "LargestAscInterval"
LARGEST_ASC_INTERVAL_SEMITONES = "LargestAscIntervalSemitones"
LARGEST_DESC_INTERVAL = "LargestDescInterval"
LARGEST_DESC_INTERVAL_SEMITONES = "LargestDescIntervalSemitones"
SMALLEST_ASC_INTERVAL = "SmallestAscInterval"
SMALLEST_ASC_INTERVAL_SEMITONES = "SmallestAscIntervalSemitones"
SMALLEST_DESC_INTERVAL = "SmallestDescInterval"
SMALLEST_DESC_INTERVAL_SEMITONES = "SmallestDescIntervalSemitones"


ALL_FEATURES = [
    INTERVALLIC_MEAN, INTERVALLIC_STD, ABSOLUTE_INTERVALLIC_MEAN, ABSOLUTE_INTERVALLIC_STD, TRIMMED_INTERVALLIC_MEAN, TRIMMED_INTERVALLIC_STD,
    TRIMMED_ABSOLUTE_INTERVALLIC_MEAN, TRIMMED_ABSOLUTE_INTERVALLIC_STD, ABSOLUTE_INTERVALLIC_TRIM_DIFF, ABSOLUTE_INTERVALLIC_TRIM_RATIO,
    ASCENDING_INTERVALS_COUNT, DESCENDING_INTERVALS_COUNT, ASCENDING_INTERVALS_PER, DESCENDING_SEMITONES,
    REPEATED_NOTES_COUNT, REPEATED_NOTES_PER, LEAPS_ASC_COUNT, LEAPS_DESC_COUNT, LEAPS_ALL_COUNT, LEAPS_ASC_PER, LEAPS_DESC_PER, LEAPS_ALL_PER,
    STEPWISE_MOTION_ASC_COUNT, STEPWISE_MOTION_DESC_COUNT, STEPWISE_MOTION_ALL_COUNT, STEPWISE_MOTION_ASC_PER, STEPWISE_MOTION_DESC_PER, STEPWISE_MOTION_ALL_PER,
    INTERVALS_PERFECT_ASC_COUNT, INTERVALS_PERFECT_DESC_COUNT, INTERVALS_PERFECT_ALL_COUNT, INTERVALS_PERFECT_ASC_PER, INTERVALS_PERFECT_DESC_PER, INTERVALS_PERFECT_ALL_PER,
    INTERVALS_MAJOR_ASC_COUNT, INTERVALS_MAJOR_DESC_COUNT, INTERVALS_MAJOR_ALL_COUNT, INTERVALS_MAJOR_ASC_PER, INTERVALS_MAJOR_DESC_PER, INTERVALS_MAJOR_ALL_PER,
    INTERVALS_MINOR_ASC_COUNT, INTERVALS_MINOR_DESC_COUNT, INTERVALS_MINOR_ALL_COUNT, INTERVALS_MINOR_ASC_PER, INTERVALS_MINOR_DESC_PER, INTERVALS_MINOR_ALL_PER,
    INTERVALS_AUGMENTED_ASC_COUNT, INTERVALS_AUGMENTED_DESC_COUNT, INTERVALS_AUGMENTED_ALL_COUNT, INTERVALS_AUGMENTED_ASC_PER, INTERVALS_AUGMENTED_DESC_PER, INTERVALS_AUGMENTED_ALL_PER,
    INTERVALS_DIMINISHED_ASC_COUNT, INTERVALS_DIMINISHED_DESC_COUNT, INTERVALS_DIMINISHED_ALL_COUNT, INTERVALS_DIMINISHED_ASC_PER, INTERVALS_DIMINISHED_DESC_PER, INTERVALS_DIMINISHED_ALL_PER,
    INTERVALS_DOUBLE_AUGMENTED_ALL_COUNT, INTERVALS_DOUBLE_AUGMENTED_ASC_COUNT, INTERVALS_DOUBLE_AUGMENTED_DESC_COUNT, INTERVALS_DOUBLE_AUGMENTED_ALL_PER, INTERVALS_DOUBLE_AUGMENTED_ASC_PER, INTERVALS_DOUBLE_AUGMENTED_DESC_PER,
    INTERVALS_DOUBLE_DIMINISHED_ALL_COUNT, INTERVALS_DOUBLE_DIMINISHED_ASC_COUNT, INTERVALS_DOUBLE_DIMINISHED_DESC_COUNT, INTERVALS_DOUBLE_DIMINISHED_ALL_PER, INTERVALS_DOUBLE_DIMINISHED_ASC_PER, INTERVALS_DOUBLE_DIMINISHED_DESC_PER,
    LARGEST_ASC_INTERVAL, LARGEST_ASC_INTERVAL_SEMITONES, LARGEST_DESC_INTERVAL, LARGEST_DESC_INTERVAL_SEMITONES,
    SMALLEST_ASC_INTERVAL, SMALLEST_ASC_INTERVAL_SEMITONES, SMALLEST_DESC_INTERVAL, SMALLEST_DESC_INTERVAL_SEMITONES,
]


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:
    numeric_intervals = part_data["numeric_intervals"]
    text_intervals = part_data["text_intervals"]
    text_intervals_count = Counter(text_intervals)

    features = {}
    features.update(get_interval_features(numeric_intervals))
    features.update(get_interval_count_features(text_intervals_count))
    features.update(get_interval_type_features(text_intervals_count))
    features.update(get_interval_stats_features(text_intervals_count))

    return features


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:

    parts_data = filter_parts_data(parts_data, score_data["parts_filter"])
    if len(parts_data) == 0:
        return {}

    features = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part_prefix = get_part_prefix(part_data["abbreviation"])
        numeric_intervals = [interval for part_data in parts_data for interval in part_data["numeric_intervals"]]
        text_intervals = [interval for part_data in parts_data for interval in part_data["text_intervals"]]
        text_intervals_count = Counter(text_intervals)
        features.update(get_interval_features(numeric_intervals, part_prefix))
        features.update(get_interval_count_features(text_intervals_count, part_prefix))
        features.update(get_interval_type_features(text_intervals_count, part_prefix))
        features.update(get_interval_stats_features(text_intervals_count, part_prefix))
        for feature_name in ALL_FEATURES:
            features[f"{part_prefix}{feature_name}"] = part_features[feature_name]

    parts_data_per_sound = {part_data["sound_abbreviation"]: [] for part_data in parts_data}
    for part_data in parts_data:
        sound = part_data["sound_abbreviation"]
        parts_data_per_sound[sound].append(part_data)
    for sound, parts_data in parts_data_per_sound.items():
        sound_prefix = get_sound_prefix(sound)
        numeric_intervals = [interval for part_data in parts_data for interval in part_data["numeric_intervals"]]
        text_intervals = [interval for part_data in parts_data for interval in part_data["text_intervals"]]
        text_intervals_count = Counter(text_intervals)
        features.update(get_interval_features(numeric_intervals, sound_prefix))
        features.update(get_interval_count_features(text_intervals_count, sound_prefix))
        features.update(get_interval_type_features(text_intervals_count, sound_prefix))
        features.update(get_interval_stats_features(text_intervals_count, sound_prefix))

    numeric_intervals = [interval for part_data in parts_data for interval in part_data["numeric_intervals"]]
    text_intervals = [interval for part_data in parts_data for interval in part_data["text_intervals"]]
    text_intervals_count = Counter(text_intervals)
    score_prefix = get_score_prefix()
    features.update(get_interval_features(numeric_intervals, score_prefix))
    features.update(get_interval_count_features(text_intervals_count, score_prefix))
    features.update(get_interval_type_features(text_intervals_count, score_prefix))
    features.update(get_interval_stats_features(text_intervals_count, score_prefix))
    return features


def get_corpus_features(scores_data: List[dict], parts_data: List[dict], cfg: Configuration, scores_features: List[dict], corpus_features: dict) -> dict:
    corpus_prefix = get_corpus_prefix()
    numeric_intervals = [interval for part_data in parts_data for interval in part_data["numeric_intervals"]]
    text_intervals = [interval for part_data in parts_data for interval in part_data["text_intervals"]]
    text_intervals_count = Counter(text_intervals)

    features = {}
    features.update(get_interval_features(numeric_intervals, corpus_prefix))
    features.update(get_interval_count_features(text_intervals_count, corpus_prefix))
    features.update(get_interval_type_features(text_intervals_count, corpus_prefix))
    features.update(get_interval_stats_features(text_intervals_count, corpus_prefix))
    return features


def get_interval_features(numeric_intervals: List[int], prefix: str = ""):
    numeric_intervals = sorted(numeric_intervals)
    interval_mean = mean(numeric_intervals) if len(numeric_intervals) > 0 else 0
    interval_std = stdev(numeric_intervals) if len(numeric_intervals) > 0 else 0
    absolute_numeric_intervals = sorted([abs(interval) for interval in numeric_intervals])
    absolute_interval_mean = mean(absolute_numeric_intervals) if len(absolute_numeric_intervals) > 0 else 0
    absolute_interval_std = stdev(absolute_numeric_intervals) if len(absolute_numeric_intervals) > 0 else 0

    cutoff = 0.1
    cutoff_elements = int(cutoff * len(numeric_intervals))
    trimmed_intervals = numeric_intervals[cutoff_elements:len(numeric_intervals) - cutoff_elements] if len(numeric_intervals) > 0 else []
    trimmed_interval_mean = mean(trimmed_intervals) if len(trimmed_intervals) > 0 else 0
    trimmed_interval_std = stdev(trimmed_intervals) if len(trimmed_intervals) > 0 else 0
    trimmed_absolute_intervals = absolute_numeric_intervals[cutoff_elements:len(numeric_intervals) - cutoff_elements] if len(absolute_numeric_intervals) > 0 else []
    trimmed_absolute_interval_mean = mean(trimmed_absolute_intervals) if len(trimmed_absolute_intervals) > 0 else 0
    trimmed_absolute_interval_std = stdev(trimmed_absolute_intervals) if len(trimmed_absolute_intervals) > 0 else 0
    trim_diff = interval_mean - trimmed_interval_mean
    trim_ratio = trim_diff / interval_mean if interval_mean != 0 else 0
    absolute_trim_diff = absolute_interval_mean - trimmed_absolute_interval_mean
    absolute_trim_ratio = absolute_trim_diff / absolute_interval_mean if absolute_interval_mean != 0 else 0
    ascending_intervals = len([interval for interval in numeric_intervals if interval > 0])
    descending_intervals = len([interval for interval in numeric_intervals if interval < 0])
    ascending_semitones = sum([interval for interval in numeric_intervals if interval > 0])
    descending_semitones = sum([interval for interval in numeric_intervals if interval < 0])
    largest_ascending_semitones = max([interval for interval in numeric_intervals if interval > 0])
    largest_ascending = Interval(largest_ascending_semitones).directedName
    largest_descending_semitones = min([interval for interval in numeric_intervals if interval < 0])
    largest_descending = Interval(largest_descending_semitones).directedName
    smallest_ascending_semitones = min([interval for interval in numeric_intervals if interval > 0])
    smallest_ascending = Interval(smallest_ascending_semitones).directedName
    smallest_descending_semitones = max([interval for interval in numeric_intervals if interval < 0])
    smallest_descending = Interval(smallest_descending_semitones).directedName
    ascending_intervals_percentage = ascending_intervals / len(numeric_intervals)
    descending_intervals_percentage = descending_intervals / len(numeric_intervals)

    features = {
        f"{prefix}{INTERVALLIC_MEAN}": interval_mean,
        f"{prefix}{INTERVALLIC_STD}": interval_std,
        f"{prefix}{ABSOLUTE_INTERVALLIC_MEAN}": absolute_interval_mean,
        f"{prefix}{ABSOLUTE_INTERVALLIC_STD}": absolute_interval_std,
        f"{prefix}{TRIMMED_INTERVALLIC_MEAN}": trimmed_interval_mean,
        f"{prefix}{TRIMMED_INTERVALLIC_STD}": trimmed_interval_std,
        f"{prefix}{TRIMMED_ABSOLUTE_INTERVALLIC_MEAN}": trimmed_absolute_interval_mean,
        f"{prefix}{TRIMMED_ABSOLUTE_INTERVALLIC_STD}": trimmed_absolute_interval_std,
        f"{prefix}{INTERVALLIC_TRIM_DIFF}": trim_diff,
        f"{prefix}{INTERVALLIC_TRIM_RATIO}": trim_ratio,
        f"{prefix}{ABSOLUTE_INTERVALLIC_TRIM_DIFF}": absolute_trim_diff,
        f"{prefix}{ABSOLUTE_INTERVALLIC_TRIM_RATIO}": absolute_trim_ratio,
        f"{prefix}{ASCENDING_INTERVALS_COUNT}": ascending_intervals,
        f"{prefix}{DESCENDING_INTERVALS_COUNT}": descending_intervals,
        f"{prefix}{ASCENDING_SEMITONES}": ascending_semitones,
        f"{prefix}{DESCENDING_SEMITONES}": descending_semitones,
        f"{prefix}{ASCENDING_INTERVALS_PER}": ascending_intervals_percentage,
        f"{prefix}{DESCENDING_INTERVALS_PER}": descending_intervals_percentage,
        f"{prefix}{LARGEST_ASC_INTERVAL}": largest_ascending,
        f"{prefix}{LARGEST_ASC_INTERVAL_SEMITONES}": largest_ascending_semitones,
        f"{prefix}{LARGEST_DESC_INTERVAL}": largest_descending,
        f"{prefix}{LARGEST_DESC_INTERVAL_SEMITONES}": largest_descending_semitones,
        f"{prefix}{SMALLEST_ASC_INTERVAL}": smallest_ascending,
        f"{prefix}{SMALLEST_ASC_INTERVAL_SEMITONES}": smallest_ascending_semitones,
        f"{prefix}{SMALLEST_DESC_INTERVAL}": smallest_descending,
        f"{prefix}{SMALLEST_DESC_INTERVAL_SEMITONES}": smallest_descending_semitones,
    }
    return features


def get_interval_count_features(interval_counts: Dict[str, int], prefix: str = "") -> dict:
    return {f"{prefix}Interval_{interval}": count for interval, count in interval_counts.items()}


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

    return {
        f"{prefix}{REPEATED_NOTES_COUNT}": no_semitones_data,
        f"{prefix}{REPEATED_NOTES_PER}": no_semitones_data / all_intervals,
        f"{prefix}{LEAPS_ASC_COUNT}": ascending_leaps,
        f"{prefix}{LEAPS_DESC_COUNT}": descending_leaps,
        f"{prefix}{LEAPS_ALL_COUNT}": ascending_leaps + descending_leaps,
        f"{prefix}{LEAPS_ASC_PER}": ascending_leaps / all_intervals,
        f"{prefix}{LEAPS_DESC_PER}": descending_leaps / all_intervals,
        f"{prefix}{LEAPS_ALL_PER}": (ascending_leaps + descending_leaps) / all_intervals,
        f"{prefix}{STEPWISE_MOTION_ASC_COUNT}": ascending_stepwise,
        f"{prefix}{STEPWISE_MOTION_DESC_COUNT}": descending_stepwise,
        f"{prefix}{STEPWISE_MOTION_ALL_COUNT}": ascending_stepwise + descending_stepwise,
        f"{prefix}{STEPWISE_MOTION_ASC_PER}": ascending_stepwise / all_intervals,
        f"{prefix}{STEPWISE_MOTION_DESC_PER}": descending_stepwise / all_intervals,
        f"{prefix}{STEPWISE_MOTION_ALL_PER}": (ascending_stepwise + descending_stepwise) / all_intervals,
        f"{prefix}{INTERVALS_PERFECT_ASC_COUNT}": ascending_perfect,
        f"{prefix}{INTERVALS_PERFECT_DESC_COUNT}": descending_perfect,
        f"{prefix}{INTERVALS_PERFECT_ALL_COUNT}": ascending_perfect + descending_perfect,
        f"{prefix}{INTERVALS_PERFECT_ASC_PER}": ascending_perfect / all_intervals,
        f"{prefix}{INTERVALS_PERFECT_DESC_PER}": descending_perfect / all_intervals,
        f"{prefix}{INTERVALS_PERFECT_ALL_PER}": (ascending_perfect + descending_perfect) / all_intervals,
        f"{prefix}{INTERVALS_MAJOR_ASC_COUNT}": ascending_major,
        f"{prefix}{INTERVALS_MAJOR_DESC_COUNT}": descending_major,
        f"{prefix}{INTERVALS_MAJOR_ALL_COUNT}": ascending_major + descending_major,
        f"{prefix}{INTERVALS_MAJOR_ASC_PER}": ascending_major / all_intervals,
        f"{prefix}{INTERVALS_MAJOR_DESC_PER}": descending_major / all_intervals,
        f"{prefix}{INTERVALS_MAJOR_ALL_PER}": (ascending_major + descending_major) / all_intervals,
        f"{prefix}{INTERVALS_MINOR_ASC_COUNT}": ascending_minor,
        f"{prefix}{INTERVALS_MINOR_DESC_COUNT}": descending_minor,
        f"{prefix}{INTERVALS_MINOR_ALL_COUNT}": ascending_minor + descending_minor,
        f"{prefix}{INTERVALS_MINOR_ASC_PER}": ascending_minor / all_intervals,
        f"{prefix}{INTERVALS_MINOR_DESC_PER}": descending_minor / all_intervals,
        f"{prefix}{INTERVALS_MINOR_ALL_PER}": (ascending_minor + descending_minor) / all_intervals,
        f"{prefix}{INTERVALS_AUGMENTED_ASC_COUNT}": ascending_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_DESC_COUNT}": descending_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_ALL_COUNT}": ascending_augmented + descending_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_ASC_PER}": ascending_augmented / all_intervals,
        f"{prefix}{INTERVALS_AUGMENTED_DESC_PER}": descending_augmented / all_intervals,
        f"{prefix}{INTERVALS_AUGMENTED_ALL_PER}": (ascending_augmented + descending_augmented) / all_intervals,
        f"{prefix}{INTERVALS_DIMINISHED_ASC_COUNT}": ascending_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_DESC_COUNT}": descending_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_ALL_COUNT}": ascending_diminished + descending_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_ASC_PER}": ascending_diminished / all_intervals,
        f"{prefix}{INTERVALS_DIMINISHED_DESC_PER}": descending_diminished / all_intervals,
        f"{prefix}{INTERVALS_DIMINISHED_ALL_PER}": (ascending_diminished + descending_diminished) / all_intervals,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ASC_COUNT}": ascending_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_DESC_COUNT}": descending_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ALL_COUNT}": ascending_double_augmented + descending_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ASC_PER}": ascending_double_augmented / all_intervals,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_DESC_PER}": descending_double_augmented / all_intervals,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ALL_PER}": (ascending_double_augmented + descending_double_augmented) / all_intervals,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ASC_COUNT}": ascending_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_DESC_COUNT}": descending_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ALL_COUNT}": ascending_double_diminished + descending_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ASC_PER}": ascending_double_diminished / all_intervals,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_DESC_PER}": descending_double_diminished / all_intervals,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ALL_PER}": (ascending_double_diminished + descending_double_diminished) / all_intervals,
    }


def get_ascending_descending(intervals_count: Dict[str, int], names: List[str]) -> Tuple[int, int]:
    ascending_data = sum([intervals_count.get(name, 0) for name in names if '-' not in name])
    descending_data = sum([intervals_count.get(name, 0) for name in names if '-' in name])
    return ascending_data, descending_data


def get_interval_stats_features(intervals_count: Dict[str, int], prefix: str = ""):
    intervals = []
    for interval, frequency in intervals_count.items():
        interval_semitones = Interval(interval).semitones
        for i in range(frequency):
            intervals.append(interval_semitones)
    intervals = np.array(intervals)
    intervals_skewness = skew(intervals)
    intervals_kurtosis = kurtosis(intervals)
    return {
        f"{prefix}{INTERVALS_SKEWNESS}": intervals_skewness,
        f"{prefix}{INTERVALS_KURTOSIS}": intervals_kurtosis,
    }
