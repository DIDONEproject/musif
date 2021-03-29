from collections import Counter
from copy import deepcopy
from statistics import mean, stdev
from typing import Dict, List, Tuple

from music21.interval import Interval
from scipy.stats import trim_mean

from musif.config import Configuration


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:
    part_suffix = f"Part{part_data['abbreviation']}"
    numeric_intervals = part_data["numeric_intervals"]
    text_intervals = part_data["text_intervals"]
    text_intervals_count = Counter(text_intervals)

    features = {}
    features.update(get_interval_features(numeric_intervals, part_suffix))
    features.update(text_intervals_count)
    features.update(get_interval_type_features(text_intervals_count, part_suffix))

    return features


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    numeric_intervals = [interval for part_data in parts_data for interval in part_data["numeric_intervals"]]
    text_intervals = [interval for part_data in parts_data for interval in part_data["text_intervals"]]
    text_intervals_count = Counter(text_intervals)

    features = {}
    features.update(get_interval_features(numeric_intervals, "Score"))
    features.update(text_intervals_count)
    features.update(get_interval_type_features(text_intervals_count, "Score"))

    return features


def get_global_features(numeric_intervals, text_intervals) -> dict:
    text_intervals_count = Counter(text_intervals)

    features = {}
    features.update(get_interval_features(numeric_intervals))
    features.update(text_intervals_count)
    features.update(get_interval_type_features(text_intervals_count))

    return features


def get_aggregated_parts_features(parts_features: List[dict], parts_data: List[dict]) -> List[dict]:
    parts_features = deepcopy(parts_features)

    # df = DataFrame(parts_features)
    # aggregation_dict = {
    #     "AscendingSemitones": "sum",
    #     "Measures": "sum",
    #     "SoundingMeasures": "sum"
    # }
    # df_sound = df.groupby("SoundAbbreviation").aggregate({"AscendingSemitones": "sum", "Measures": "sum", "SoundingMeasures": "sum"})
    # df_family = df.groupby("FamilyAbbreviation").aggregate({"AscendingSemitones": "sum", "Measures": "sum", "SoundingMeasures": "sum"})
    #
    # "IntervallicRatio": interval_ratio,
    # "TrimmedIntervallicRatio": trimmed_interval_ratio,
    # "TrimmedDiff": trim_diff,
    # "TrimRatio": trim_ratio,
    # "AbsoluteIntervallicRatio": absolute_interval_mean,
    # "Std": interval_std,
    # "AbsoluteStd": absolute_interval_std,
    # "AscendingSemitones": ascending_semitones,
    # "AscendingInterval": ascending_semitones_name,
    # "DescendingSemitones": descending_semitones,
    # "DescendingInterval": descending_semitones_name,
    #
    # features.update(get_interval_aggregated_features(parts_features))
    # features.update(get_interval_type_aggregated_features(parts_features))

    return parts_features


def get_interval_features(numeric_intervals: List[int], prefix: str):
    interval_mean = mean(numeric_intervals)
    interval_std = stdev(numeric_intervals)
    absolute_numeric_intervals = [abs(interval) for interval in numeric_intervals]
    absolute_interval_mean = mean(absolute_numeric_intervals)
    absolute_interval_std = stdev(absolute_numeric_intervals)

    trimmed_absolute_interval_mean = trim_mean(absolute_numeric_intervals, 0.1)
    trim_diff = absolute_interval_mean - trimmed_absolute_interval_mean
    trim_ratio = trim_diff / absolute_interval_mean
    ascending_semitones = max(numeric_intervals)
    ascending_semitones_name = Interval(ascending_semitones).directedName
    descending_semitones = min(numeric_intervals)
    descending_semitones_name = Interval(descending_semitones).directedName

    features = {
        f"{prefix}IntervallicMean": interval_mean,
        f"{prefix}IntervallicStd": interval_std,
        f"{prefix}AbsoluteIntervallicMean": absolute_interval_mean,
        f"{prefix}AbsoluteIntervallicStd": absolute_interval_std,
        f"{prefix}TrimmedAbsoluteIntervallicRatio": trimmed_absolute_interval_mean,
        f"{prefix}AbsoluteIntervallicTrimDiff": trim_diff,
        f"{prefix}AbsoluteIntervallicTrimRatio": trim_ratio,
        f"{prefix}AscendingSemitones": ascending_semitones,
        f"{prefix}AscendingInterval": ascending_semitones_name,
        f"{prefix}DescendingSemitones": descending_semitones,
        f"{prefix}DescendingInterval": descending_semitones_name,
    }

    return features


def get_interval_type_features(intervals_count: Dict[str, int], prefix: str):
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
    ascending_leaps_data, descending_leaps_data = get_ascending_descending(intervals_count, leaps)

    # Stepwise motion (no. semitones is 1 or 2)
    stepwise = [iname for iname in intervals_names if Interval(iname).semitones in [1, -1, 2, -2]]
    ascending_stepwise_data, descending_stepwise_data = get_ascending_descending(intervals_count, stepwise)

    # PERFECT
    perfect = [iname for iname in intervals_names if 'P' in iname or 'p' in iname]
    ascending_perfect_data, descending_perfect_data = get_ascending_descending(intervals_count, perfect)

    # MAJOR
    major = [iname for iname in intervals_names if 'M' in iname]
    ascending_mayor_data, descending_mayor_data = get_ascending_descending(intervals_count, major)

    # MINOR
    minor = [iname for iname in intervals_names if 'm' in iname]
    ascending_minor_data, descending_minor_data = get_ascending_descending(intervals_count, minor)

    # AUGMENTED
    aug = [iname for iname in intervals_names if 'A' in iname]
    ascending_aug_data, descending_aug_data = get_ascending_descending(intervals_count, aug)

    # DIMINISHED
    dimi = [iname for iname in intervals_names if 'd' in iname]
    ascending_dimi_data, descending_dimi_data = get_ascending_descending(intervals_count, dimi)

    return {
        f"{prefix}RepeatedNotes": no_semitones_data,
        f"{prefix}LeapsAscending": ascending_leaps_data,
        f"{prefix}LeapsDescending": descending_leaps_data,
        f"{prefix}LeapsAll": sum([ascending_leaps_data, descending_leaps_data]),
        f"{prefix}StepwiseMotionAscending": ascending_stepwise_data,
        f"{prefix}StepwiseMotionDescending": descending_stepwise_data,
        f"{prefix}StepwiseMotionAll": sum([ascending_stepwise_data, descending_stepwise_data]),
        f"{prefix}Total": sum([ascending_leaps_data, descending_leaps_data]) + sum([ascending_leaps_data, descending_leaps_data]),
        f"{prefix}PerfectAscending": ascending_perfect_data,
        f"{prefix}PerfectDescending": descending_perfect_data,
        f"{prefix}PerfectAll": sum([ascending_perfect_data, descending_perfect_data]),
        f"{prefix}MajorAscending": ascending_mayor_data,
        f"{prefix}MajorDescending": descending_mayor_data,
        f"{prefix}MajorAll": sum([ascending_mayor_data, descending_mayor_data]),
        f"{prefix}MinorAscending": ascending_minor_data,
        f"{prefix}MinorDescending": descending_minor_data,
        f"{prefix}MinorAll": sum([ascending_minor_data, descending_minor_data]),
        f"{prefix}AugmentedAscending": ascending_aug_data,
        f"{prefix}AugmentedDescending": descending_aug_data,
        f"{prefix}AugmentedAll": sum([ascending_aug_data, descending_aug_data]),
        f"{prefix}DiminishedAscending": ascending_dimi_data,
        f"{prefix}DiminishedDescending": descending_dimi_data,
        f"{prefix}DiminishedAll": sum([ascending_dimi_data, descending_dimi_data]),
        f"{prefix}Total1": sum([ascending_perfect_data, descending_perfect_data])
                           + sum([ascending_mayor_data, descending_mayor_data])
                           + sum([ascending_minor_data, descending_minor_data])
                           + sum([ascending_aug_data, descending_aug_data])
                           + sum([ascending_dimi_data, descending_dimi_data])
    }


def get_ascending_descending(intervals_count: Dict[str, int], names: List[str]) -> Tuple[int, int]:
    ascending_data = sum([intervals_count.get(name, 0) for name in names if '-' not in name])
    descending_data = sum([intervals_count.get(name, 0) for name in names if '-' in name])
    return ascending_data, descending_data
