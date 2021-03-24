from collections import Counter
from statistics import mean, stdev
from typing import Dict, List, Tuple

from music21.interval import Interval
from scipy.stats import trim_mean

from musif.musicxml import get_intervals, Note


def get_single_part_features(notes: List[Note]) -> dict:
    numeric_intervals, text_intervals = get_intervals(notes)
    text_intervals_count = Counter(text_intervals)

    features = {}
    features.update(get_interval_features(numeric_intervals))
    features.update(text_intervals_count)
    features.update(get_interval_type_features(text_intervals_count))

    return features


def get_interval_features(numeric_intervals: List[int]):
    absolute_numeric_intervals = [abs(interval) for interval in numeric_intervals]

    ##############################
    # Statistical_values (sheet1) #
    ##############################
    # Stats with absolute values, i.e. negative intervals are switched to positive
    interval_ratio = round(mean(absolute_numeric_intervals), 3)
    trimmed_interval_ratio = round(trim_mean(absolute_numeric_intervals, 0.1), 3)
    trim_diff = round(interval_ratio - trimmed_interval_ratio, 3)
    trim_ratio = round(trim_diff / interval_ratio, 3)
    interval_mean = round(mean(numeric_intervals), 3)
    interval_std = round(stdev(numeric_intervals), 3)
    absolute_interval_mean = round(mean(absolute_numeric_intervals), 3)
    absolute_interval_std = round(stdev(absolute_numeric_intervals), 3)

    #########################
    # Largest_leaps (sheet3) #
    #########################
    ascending_semitones = max(numeric_intervals)
    ascending_semitones_name = Interval(ascending_semitones).directedName
    descending_semitones = min(numeric_intervals)
    descending_semitones_name = Interval(descending_semitones).directedName

    return {
        "IntervallicRatio": interval_ratio,
        "TrimmedIntervallicRatio": trimmed_interval_ratio,
        "TrimmedDiff": trim_diff,
        "TrimRatio": trim_ratio,
        "AbsoluteIntervallicRatio": absolute_interval_mean,
        "Std": interval_std,
        "AbsoluteStd": absolute_interval_std,
        "AscendingSemitones": ascending_semitones,
        "AscendingInterval": ascending_semitones_name,
        "DescendingSemitones": descending_semitones,
        "DescendingInterval": descending_semitones_name,
    }


def get_interval_type_features(intervals_count: Dict[str, int]):
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

    return {"RepeatedNotes": no_semitones_data,
            "LeapsAscending": ascending_leaps_data,
            "LeapsDescending": descending_leaps_data,
            "LeapsAll": sum([ascending_leaps_data, descending_leaps_data]),
            "StepwiseMotionAscending": ascending_stepwise_data,
            "StepwiseMotionDescending": descending_stepwise_data,
            "StepwiseMotionAll": sum([ascending_stepwise_data, descending_stepwise_data]),
            "Total": sum([ascending_leaps_data, descending_leaps_data]) + sum([ascending_leaps_data, descending_leaps_data]),
            "PerfectAscending": ascending_perfect_data,
            "PerfectDescending": descending_perfect_data,
            "PerfectAll": sum([ascending_perfect_data, descending_perfect_data]),
            "MajorAscending": ascending_mayor_data,
            "MajorDescending": descending_mayor_data,
            "MajorAll": sum([ascending_mayor_data, descending_mayor_data]),
            "MinorAscending": ascending_minor_data,
            "MinorDescending": descending_minor_data,
            "MinorAll": sum([ascending_minor_data, descending_minor_data]),
            "AugmentedAscending": ascending_aug_data,
            "AugmentedDescending": descending_aug_data,
            "AugmentedAll": sum([ascending_aug_data, descending_aug_data]),
            "DiminishedAscending": ascending_dimi_data,
            "DiminishedDescending": descending_dimi_data,
            "DiminishedAll": sum([ascending_dimi_data, descending_dimi_data]),
            "Total1": sum([ascending_perfect_data, descending_perfect_data]) + sum([ascending_mayor_data, descending_mayor_data])
                      + sum([ascending_minor_data, descending_minor_data]) + sum([ascending_aug_data, descending_aug_data])
                      + sum([ascending_dimi_data, descending_dimi_data])
            }


def get_ascending_descending(intervals_count: Dict[str, int], names: List[str]) -> Tuple[int, int]:
    ascending_data = sum([intervals_count.get(name, 0) for name in names if '-' not in name])
    descending_data = sum([intervals_count.get(name, 0) for name in names if '-' in name])
    return ascending_data, descending_data
