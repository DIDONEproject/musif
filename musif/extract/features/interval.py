from collections import Counter
from statistics import mean, stdev
from typing import Dict, List, Tuple

from music21.interval import Interval

from musif.config import Configuration
from musif.extract.features.prefix import get_score_prefix, get_part_prefix, get_corpus_prefix

INTERVALLIC_MEAN = "IntervallicRatio"
INTERVALLIC_STD = "IntervallicStd"
ABSOLUTE_INTERVALLIC_MEAN = "AbsoluteIntervallicRatio"
ABSOLUTE_INTERVALLIC_STD = "AbsoluteIntervallicStd"
TRIMMED_INTERVALLIC_MEAN = "TrimmedIntervallicRatio"
TRIMMED_INTERVALLIC_STD = "TrimmedIntervallicStd"
TRIMMED_ABSOLUTE_INTERVALLIC_MEAN = "TrimmedAbsoluteIntervallicRatio"
TRIMMED_ABSOLUTE_INTERVALLIC_STD = "TrimmedAbsoluteIntervallicStd"
ABSOLUTE_INTERVALLIC_TRIM_DIFF = "AbsoluteIntervallicTrimDiff"
ABSOLUTE_INTERVALLIC_TRIM_RATIO = "AbsoluteIntervallicTrimRatio"
ASCENDING_SEMITONES = "AscendingSemitones"
ASCENDING_INTERVAL = "AscendingInterval"
DESCENDING_SEMITONES = "DescendingSemitones"
DESCENDING_INTERVAL = "DescendingInterval"
REPEATED_NOTES = "RepeatedNotes"
LEAPS_ASCENDING = "LeapsAscending"
LEAPS_DESCENDING = "LeapsDescending"
LEAPS_ALL = "LeapsAll"
STEPWISE_MOTION_ASCENDING = "StepwiseMotionAscending"
STEPWISE_MOTION_DESCENDING = "StepwiseMotionDescending"
STEPWISE_MOTION_ALL = "StepwiseMotionAll"
LEAPS_STEPWISE_MOTION_TOTAL = "LeapsStepwiseMotionTotal"
INTERVALS_PERFECT_ASCENDING = "IntervalsPerfectAscending"
INTERVALS_PERFECT_DESCENDING = "IntervalsPerfectDescending"
INTERVALS_PERFECT_ALL = "IntervalsPerfectAll"
INTERVALS_MAJOR_ASCENDING = "IntervalsMajorAscending"
INTERVALS_MAJOR_DESCENDING = "IntervalsMajorDescending"
INTERVALS_MAJOR_ALL = "IntervalsMajorAll"
INTERVALS_MINOR_ASCENDING = "IntervalsMinorAscending"
INTERVALS_MINOR_DESCENDING = "IntervalsMinorDescending"
INTERVALS_MINOR_ALL = "IntervalsMinorAll"
INTERVALS_AUGMENTED_ASCENDING = "IntervalsAugmentedAscending"
INTERVALS_AUGMENTED_DESCENDING = "IntervalsAugmentedDescending"
INTERVALS_AUGMENTED_ALL = "IntervalsAugmentedAll"
INTERVALS_DIMINISHED_ASCENDING = "IntervalsDiminishedAscending"
INTERVALS_DIMINISHED_DESCENDING = "IntervalsDiminishedDescending"
INTERVALS_DIMINISHED_ALL = "IntervalsDiminishedAll"

ALL_FEATURES = [
    INTERVALLIC_MEAN, INTERVALLIC_STD, ABSOLUTE_INTERVALLIC_MEAN, ABSOLUTE_INTERVALLIC_STD, TRIMMED_INTERVALLIC_MEAN, TRIMMED_INTERVALLIC_STD,
    TRIMMED_ABSOLUTE_INTERVALLIC_MEAN, TRIMMED_ABSOLUTE_INTERVALLIC_STD, ABSOLUTE_INTERVALLIC_TRIM_DIFF, ABSOLUTE_INTERVALLIC_TRIM_RATIO,
    ASCENDING_SEMITONES, ASCENDING_INTERVAL, DESCENDING_SEMITONES, DESCENDING_INTERVAL,
    REPEATED_NOTES, LEAPS_ASCENDING, LEAPS_DESCENDING, LEAPS_ALL, STEPWISE_MOTION_ASCENDING, STEPWISE_MOTION_DESCENDING, STEPWISE_MOTION_ALL,
    LEAPS_STEPWISE_MOTION_TOTAL, INTERVALS_PERFECT_ASCENDING, INTERVALS_PERFECT_DESCENDING, INTERVALS_PERFECT_ALL, INTERVALS_MAJOR_ASCENDING,
    INTERVALS_MAJOR_DESCENDING, INTERVALS_MAJOR_ALL, INTERVALS_MINOR_ASCENDING, INTERVALS_MINOR_DESCENDING, INTERVALS_MINOR_ALL,
    INTERVALS_AUGMENTED_ASCENDING, INTERVALS_AUGMENTED_DESCENDING, INTERVALS_AUGMENTED_ALL, INTERVALS_DIMINISHED_ASCENDING, INTERVALS_DIMINISHED_DESCENDING,
    INTERVALS_DIMINISHED_ALL]


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:
    numeric_intervals = part_data["numeric_intervals"]
    text_intervals = part_data["text_intervals"]
    text_intervals_count = Counter(text_intervals)

    features = {}
    features.update(get_interval_features(numeric_intervals))
    features.update(get_interval_count_features(text_intervals_count))
    features.update(get_interval_type_features(text_intervals_count))

    return features


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    if len(parts_data) == 0:
        return {}
    score_prefix = get_score_prefix()
    numeric_intervals = [interval for part_data in parts_data for interval in part_data["numeric_intervals"]]
    text_intervals = [interval for part_data in parts_data for interval in part_data["text_intervals"]]
    text_intervals_count = Counter(text_intervals)

    features = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part_prefix = get_part_prefix(part_data["abbreviation"])
        for feature_name in ALL_FEATURES:
            features[f"{part_prefix}{feature_name}"] = part_features[feature_name]
    features.update(get_interval_features(numeric_intervals, score_prefix))
    features.update(get_interval_count_features(text_intervals_count, score_prefix))
    features.update(get_interval_type_features(text_intervals_count, score_prefix))
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
    trim_diff = absolute_interval_mean - trimmed_absolute_interval_mean
    trim_ratio = trim_diff / absolute_interval_mean if absolute_interval_mean != 0 else 0
    ascending_semitones = max(numeric_intervals) if len(numeric_intervals) > 0 else None
    ascending_semitones_name = Interval(ascending_semitones).directedName if ascending_semitones is not None else None
    descending_semitones = min(numeric_intervals) if len(numeric_intervals) > 0 else None
    descending_semitones_name = Interval(descending_semitones).directedName if descending_semitones is not None else None

    features = {
        f"{prefix}{INTERVALLIC_MEAN}": interval_mean,
        f"{prefix}{INTERVALLIC_STD}": interval_std,
        f"{prefix}{ABSOLUTE_INTERVALLIC_MEAN}": absolute_interval_mean,
        f"{prefix}{ABSOLUTE_INTERVALLIC_STD}": absolute_interval_std,
        f"{prefix}{TRIMMED_INTERVALLIC_MEAN}": trimmed_interval_mean,
        f"{prefix}{TRIMMED_INTERVALLIC_STD}": trimmed_interval_std,
        f"{prefix}{TRIMMED_ABSOLUTE_INTERVALLIC_MEAN}": trimmed_absolute_interval_mean,
        f"{prefix}{TRIMMED_ABSOLUTE_INTERVALLIC_STD}": trimmed_absolute_interval_std,
        f"{prefix}{ABSOLUTE_INTERVALLIC_TRIM_DIFF}": trim_diff,
        f"{prefix}{ABSOLUTE_INTERVALLIC_TRIM_RATIO}": trim_ratio,
        f"{prefix}{ASCENDING_SEMITONES}": ascending_semitones,
        f"{prefix}{ASCENDING_INTERVAL}": ascending_semitones_name,
        f"{prefix}{DESCENDING_SEMITONES}": descending_semitones,
        f"{prefix}{DESCENDING_INTERVAL}": descending_semitones_name,
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
    no_semitones = ['P1', 'P-1', 'd2', 'd-2']
    no_semitones_data = sum([intervals_count.get(name, 0) for name in no_semitones])

    # Leaps (no. semitones >= 3)
    leaps = [iname for iname in intervals_names if Interval(iname).semitones >= 3 or Interval(iname).semitones <= -3]
    ascending_leaps, descending_leaps = get_ascending_descending(intervals_count, leaps)

    # Stepwise motion (no. semitones is 1 or 2)
    stepwise = [iname for iname in intervals_names if Interval(iname).semitones in [1, -1, 2, -2]]
    ascending_stepwise, descending_stepwise = get_ascending_descending(intervals_count, stepwise)

    perfect = [iname for iname in intervals_names if 'P' in iname or 'p' in iname]
    ascending_perfect, descending_perfect = get_ascending_descending(intervals_count, perfect)

    major = [iname for iname in intervals_names if 'M' in iname]
    ascending_mayor, descending_mayor = get_ascending_descending(intervals_count, major)

    minor = [iname for iname in intervals_names if 'm' in iname]
    ascending_minor, descending_minor = get_ascending_descending(intervals_count, minor)

    aug = [iname for iname in intervals_names if 'A' in iname]
    ascending_aug, descending_aug = get_ascending_descending(intervals_count, aug)

    dimi = [iname for iname in intervals_names if 'd' in iname]
    ascending_dimi, descending_dimi = get_ascending_descending(intervals_count, dimi)

    return {
        f"{prefix}{REPEATED_NOTES}": no_semitones_data,
        f"{prefix}{LEAPS_ASCENDING}": ascending_leaps,
        f"{prefix}{LEAPS_DESCENDING}": descending_leaps,
        f"{prefix}{LEAPS_ALL}": sum([ascending_leaps, descending_leaps]),
        f"{prefix}{STEPWISE_MOTION_ASCENDING}": ascending_stepwise,
        f"{prefix}{STEPWISE_MOTION_DESCENDING}": descending_stepwise,
        f"{prefix}{STEPWISE_MOTION_ALL}": sum([ascending_stepwise, descending_stepwise]),
        f"{prefix}{LEAPS_STEPWISE_MOTION_TOTAL}": sum([ascending_leaps, descending_leaps]) + sum([ascending_stepwise, descending_stepwise]),
        f"{prefix}{INTERVALS_PERFECT_ASCENDING}": ascending_perfect,
        f"{prefix}{INTERVALS_PERFECT_DESCENDING}": descending_perfect,
        f"{prefix}{INTERVALS_PERFECT_ALL}": sum([ascending_perfect, descending_perfect]),
        f"{prefix}{INTERVALS_MAJOR_ASCENDING}": ascending_mayor,
        f"{prefix}{INTERVALS_MAJOR_DESCENDING}": descending_mayor,
        f"{prefix}{INTERVALS_MAJOR_ALL}": sum([ascending_mayor, descending_mayor]),
        f"{prefix}{INTERVALS_MINOR_ASCENDING}": ascending_minor,
        f"{prefix}{INTERVALS_MINOR_DESCENDING}": descending_minor,
        f"{prefix}{INTERVALS_MINOR_ALL}": sum([ascending_minor, descending_minor]),
        f"{prefix}{INTERVALS_AUGMENTED_ASCENDING}": ascending_aug,
        f"{prefix}{INTERVALS_AUGMENTED_DESCENDING}": descending_aug,
        f"{prefix}{INTERVALS_AUGMENTED_ALL}": sum([ascending_aug, descending_aug]),
        f"{prefix}{INTERVALS_DIMINISHED_ASCENDING}": ascending_dimi,
        f"{prefix}{INTERVALS_DIMINISHED_DESCENDING}": descending_dimi,
        f"{prefix}{INTERVALS_DIMINISHED_ALL}": sum([ascending_dimi, descending_dimi]),
    }


def get_ascending_descending(intervals_count: Dict[str, int], names: List[str]) -> Tuple[int, int]:
    ascending_data = sum([intervals_count.get(name, 0) for name in names if '-' not in name])
    descending_data = sum([intervals_count.get(name, 0) for name in names if '-' in name])
    return ascending_data, descending_data
