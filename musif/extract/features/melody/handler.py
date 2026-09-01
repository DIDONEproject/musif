import warnings
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
from musif.extract.constants import DATA_PART_ABBREVIATION, DATA_SOUND_ABBREVIATION
from musif.extract.features.core.constants import (
    DATA_INTERVALS,
    DATA_MELODIC_LINES,
)
from musif.extract.features.prefix import (
    get_part_feature,
    get_part_prefix,
    get_score_prefix,
    get_sound_prefix,
)

from .constants import *

# speed/acceleration depend only on the sampling step; the smoothing window
# applies only to the four chunk statistics below
STEP_FEATURE_NAMES = (
    SPEED_AVG_ABS,
    ACCELERATION_AVG_ABS,
)
CHUNK_FEATURE_NAMES = (
    ASCENDENT_AVERAGE,
    DESCENDENT_AVERAGE,
    ASCENDENT_PROPORTION,
    DESCENDENT_PROPORTION,
)


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    # Interval features are recomputed per scope in update_score_objects from
    # the raw interval lists; only the motion features are needed here.
    part_features.update(get_motion_features(part_data))


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

    # Staves sharing an abbreviation are treated as one logical part: interval
    # features are recomputed from the concatenated interval lists (exactly as
    # the sound scope below does) and motion features from the concatenated
    # note stream.
    parts_by_abbreviation: Dict[str, List[Tuple[dict, dict]]] = {}
    for part_data, part_features in zip(parts_data, parts_features):
        parts_by_abbreviation.setdefault(
            part_data[DATA_PART_ABBREVIATION], []
        ).append((part_data, part_features))

    for part, group in parts_by_abbreviation.items():
        if len(group) == 1:
            motion_features = group[0][1]
        else:
            # duplicate staves: each staff's melodic lines stay separate
            # lines, so nothing is spliced across simultaneous streams
            merged_part_data = {
                DATA_MELODIC_LINES: [
                    line
                    for part_data, _ in group
                    for line in part_data[DATA_MELODIC_LINES]
                ]
            }
            motion_features = get_motion_features(merged_part_data)
        for step in MOTION_STEPS:
            step_postfix = _motion_step_postfix(step)
            for name in STEP_FEATURE_NAMES:
                features[get_part_feature(part, name + step_postfix)] = (
                    motion_features[name + step_postfix]
                )
            for win in MOTION_WINS:
                key_postfix = _motion_postfix(step, win)
                for name in CHUNK_FEATURE_NAMES:
                    features[get_part_feature(part, name + key_postfix)] = (
                        motion_features[name + key_postfix]
                    )

        part_prefix = get_part_prefix(part)
        intervals = [
            interval
            for part_data, _ in group
            for interval in part_data[DATA_INTERVALS]
        ]
        features.update(get_interval_features(intervals, part_prefix))
        features.update(get_interval_count_features(intervals, part_prefix))
        features.update(get_interval_type_features(intervals, part_prefix))
        features.update(get_interval_stats_features(intervals, part_prefix))

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

    nan = float("nan")
    absolute_intervallic_mean = (
        mean(absolute_numeric_intervals) if len(intervals) > 0 else nan
    )
    intervallic_mean = mean(numeric_intervals) if len(intervals) > 0 else nan
    ascending_intervallic_mean = (
        mean(ascending_intervals) if len(ascending_intervals) > 0 else nan
    )
    descending_intervallic_mean = (
        mean(descending_intervals) if len(descending_intervals) > 0 else nan
    )
    with np.errstate(invalid="ignore"):
        absolute_intervallic_std = (
            stdev(absolute_numeric_intervals) if len(intervals) > 1 else nan
        )
        intervallic_std = stdev(numeric_intervals) if len(intervals) > 1 else nan
        ascending_intervallic_std = (
            stdev(ascending_intervals) if len(ascending_intervals) > 1 else nan
        )
        descending_intervallic_std = (
            stdev(descending_intervals) if len(descending_intervals) > 1 else nan
        )
    # MeanInterval is the mean *absolute* interval re-spelled by music21, so it
    # never descends; see Feature_definition.md.
    mean_interval = (
        Interval(int(round(absolute_intervallic_mean))).directedName
        if len(intervals) > 0
        else None
    )

    cutoff = 0.1
    limits = (cutoff, cutoff)  # 10% trimmed from each tail
    trimmed_intervallic_mean = (
        trimmed_mean(numeric_intervals, limits) if len(intervals) > 0 else nan
    )
    trimmed_absolute_intervallic_mean = (
        trimmed_mean(absolute_numeric_intervals, limits) if len(intervals) > 0 else nan
    )
    with np.errstate(invalid="ignore"):
        trimmed_intervallic_std = (
            trimmed_std(numeric_intervals, limits, ddof=1)
            if len(intervals) > 1
            else nan
        )
        trimmed_absolute_intervallic_std = (
            trimmed_std(absolute_numeric_intervals, limits, ddof=1)
            if len(intervals) > 1
            else nan
        )
    trim_diff = intervallic_mean - trimmed_intervallic_mean
    trim_ratio = trim_diff / intervallic_mean if intervallic_mean != 0 else nan
    absolute_trim_diff = absolute_intervallic_mean - trimmed_absolute_intervallic_mean
    absolute_trim_ratio = (
        absolute_trim_diff / absolute_intervallic_mean
        if absolute_intervallic_mean != 0
        else nan
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
        num_ascending_intervals / len(intervals) if len(intervals) > 0 else nan
    )
    descending_intervals_percentage = (
        num_descending_intervals / len(intervals) if len(intervals) > 0 else nan
    )

    # Extremes are selected by magnitude and keep the notated interval object,
    # so the reported name preserves the original spelling (an A4 stays A4).
    largest_interval = (
        max(intervals, key=lambda i: abs(i.semitones)) if len(intervals) > 0 else None
    )
    largest_semitones = largest_interval.semitones if largest_interval else None
    largest = largest_interval.directedName if largest_interval else None
    ascending_objects = [i for i in intervals if i.semitones > 0]
    descending_objects = [i for i in intervals if i.semitones < 0]

    largest_ascending_interval = (
        max(ascending_objects, key=lambda i: i.semitones) if ascending_objects else None
    )
    largest_ascending_semitones = (
        largest_ascending_interval.semitones if largest_ascending_interval else None
    )
    largest_ascending = (
        largest_ascending_interval.directedName if largest_ascending_interval else None
    )
    largest_descending_interval = (
        min(descending_objects, key=lambda i: i.semitones)
        if descending_objects
        else None
    )
    largest_descending_semitones = (
        largest_descending_interval.semitones if largest_descending_interval else None
    )
    largest_descending = (
        largest_descending_interval.directedName if largest_descending_interval else None
    )
    smallest_ascending_interval = (
        min(ascending_objects, key=lambda i: i.semitones) if ascending_objects else None
    )
    smallest_ascending_semitones = (
        smallest_ascending_interval.semitones if smallest_ascending_interval else None
    )
    smallest_ascending = (
        smallest_ascending_interval.directedName if smallest_ascending_interval else None
    )
    smallest_descending_interval = (
        max(descending_objects, key=lambda i: i.semitones)
        if descending_objects
        else None
    )
    smallest_descending_semitones = (
        smallest_descending_interval.semitones if smallest_descending_interval else None
    )
    smallest_descending = (
        smallest_descending_interval.directedName
        if smallest_descending_interval
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
        f"{prefix}{SMALLEST_INTERVAL_ASC}": smallest_ascending,
        f"{prefix}{SMALLEST_INTERVAL_DESC}": smallest_descending,
        f"{prefix}{SMALLEST_SEMITONES_ASC}": smallest_ascending_semitones,
        f"{prefix}{SMALLEST_SEMITONES_DESC}": smallest_descending_semitones,
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
        # A repeated note is one whose pitch does not change (0 semitones);
        # chromatic unisons (A1/d1) move by a semitone and count as steps.
        if interval.semitones == 0:
            repeated_notes_list.append(interval)
        elif interval_number <= 2:
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
        else float("nan"),
        f"{prefix}{STEPWISE_MOTION_ASC_COUNT}": ascending_stepwise,
        f"{prefix}{STEPWISE_MOTION_DESC_COUNT}": descending_stepwise,
        f"{prefix}{STEPWISE_MOTION_ALL_COUNT}": all_stepwise,
        f"{prefix}{STEPWISE_MOTION_ASC_PER}": ascending_stepwise / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{STEPWISE_MOTION_DESC_PER}": descending_stepwise / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{STEPWISE_MOTION_ALL_PER}": all_stepwise / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{LEAPS_ASC_COUNT}": ascending_leaps,
        f"{prefix}{LEAPS_DESC_COUNT}": descending_leaps,
        f"{prefix}{LEAPS_ALL_COUNT}": all_leaps,
        f"{prefix}{LEAPS_ASC_PER}": ascending_leaps / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{LEAPS_DESC_PER}": descending_leaps / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{LEAPS_ALL_PER}": all_leaps / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_PERFECT_ASC_COUNT}": ascending_perfect,
        f"{prefix}{INTERVALS_PERFECT_DESC_COUNT}": descending_perfect,
        f"{prefix}{INTERVALS_PERFECT_ALL_COUNT}": all_perfect,
        f"{prefix}{INTERVALS_PERFECT_ASC_PER}": ascending_perfect / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_PERFECT_DESC_PER}": descending_perfect / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_PERFECT_ALL_PER}": all_perfect / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_MAJOR_ASC_COUNT}": ascending_major,
        f"{prefix}{INTERVALS_MAJOR_DESC_COUNT}": descending_major,
        f"{prefix}{INTERVALS_MAJOR_ALL_COUNT}": all_major,
        f"{prefix}{INTERVALS_MAJOR_ASC_PER}": ascending_major / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_MAJOR_DESC_PER}": descending_major / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_MAJOR_ALL_PER}": all_major / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_MINOR_ASC_COUNT}": ascending_minor,
        f"{prefix}{INTERVALS_MINOR_DESC_COUNT}": descending_minor,
        f"{prefix}{INTERVALS_MINOR_ALL_COUNT}": all_minor,
        f"{prefix}{INTERVALS_MINOR_ASC_PER}": ascending_minor / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_MINOR_DESC_PER}": descending_minor / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_MINOR_ALL_PER}": all_minor / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_AUGMENTED_ASC_COUNT}": ascending_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_DESC_COUNT}": descending_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_ALL_COUNT}": all_augmented,
        f"{prefix}{INTERVALS_AUGMENTED_ASC_PER}": ascending_augmented / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_AUGMENTED_DESC_PER}": descending_augmented / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_AUGMENTED_ALL_PER}": all_augmented / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_DIMINISHED_ASC_COUNT}": ascending_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_DESC_COUNT}": descending_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_ALL_COUNT}": all_diminished,
        f"{prefix}{INTERVALS_DIMINISHED_ASC_PER}": ascending_diminished / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_DIMINISHED_DESC_PER}": descending_diminished
        / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_DIMINISHED_ALL_PER}": all_diminished / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ASC_COUNT}": ascending_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_DESC_COUNT}": descending_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ALL_COUNT}": all_double_augmented,
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ASC_PER}": ascending_double_augmented
        / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_DESC_PER}": descending_double_augmented
        / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_DOUBLE_AUGMENTED_ALL_PER}": all_double_augmented
        / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ASC_COUNT}": ascending_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_DESC_COUNT}": descending_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ALL_COUNT}": all_double_diminished,
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ASC_PER}": ascending_double_diminished
        / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_DESC_PER}": descending_double_diminished
        / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_DOUBLE_DIMINISHED_ALL_PER}": all_double_diminished
        / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ASC_COUNT}": ascending_within_octave,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_DESC_COUNT}": descending_within_octave,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ALL_COUNT}": all_within_octave,
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ASC_PER}": ascending_within_octave
        / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_DESC_PER}": descending_within_octave
        / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_WITHIN_OCTAVE_ALL_PER}": all_within_octave / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ASC_COUNT}": ascending_beyond_octave,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_DESC_COUNT}": descending_beyond_octave,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ALL_COUNT}": all_beyond_octave,
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ASC_PER}": ascending_beyond_octave
        / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_DESC_PER}": descending_beyond_octave
        / all_intervals
        if all_intervals != 0
        else float("nan"),
        f"{prefix}{INTERVALS_BEYOND_OCTAVE_ALL_PER}": all_beyond_octave / all_intervals
        if all_intervals != 0
        else float("nan"),
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
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        # constant data makes scipy warn and return nan; nan is the wanted
        # sentinel for an undefined moment, so silence the warning
        warnings.simplefilter("ignore", RuntimeWarning)
        intervals_skewness = (
            skew(numeric_intervals, bias=False)
            if len(numeric_intervals) >= 3
            else np.nan
        )
        intervals_kurtosis = (
            kurtosis(numeric_intervals, bias=False)
            if len(numeric_intervals) >= 4
            else np.nan
        )
        absolute_intervals_skewness = (
            skew(absolute_numeric_intervals, bias=False)
            if len(absolute_numeric_intervals) >= 3
            else np.nan
        )
        absolute_intervals_kurtosis = (
            kurtosis(absolute_numeric_intervals, bias=False)
            if len(absolute_numeric_intervals) >= 4
            else np.nan
        )

    return {
        f"{prefix}{INTERVALLIC_SKEWNESS}": intervals_skewness,
        f"{prefix}{INTERVALLIC_KURTOSIS}": intervals_kurtosis,
        f"{prefix}{ABSOLUTE_INTERVALLIC_SKEWNESS}": absolute_intervals_skewness,
        f"{prefix}{ABSOLUTE_INTERVALLIC_KURTOSIS}": absolute_intervals_kurtosis,
    }


def _motion_postfix(step, win):
    return f"_step_{step}_win_{win}"


def _motion_step_postfix(step):
    return f"_step_{step}"


def _melodic_segments(lines):
    """Runs of consecutive notes per melodic line; any rest splits a line
    into segments so motion is never measured across a silence."""
    segments = []
    for line in lines:
        durations, midis = [], []
        for element in line:
            if hasattr(element, "pitch"):
                durations.append(float(element.duration.quarterLength))
                midis.append(element.pitch.midi)
            elif durations:
                segments.append((np.asarray(durations), np.asarray(midis)))
                durations, midis = [], []
        if durations:
            segments.append((np.asarray(durations), np.asarray(midis)))
    return segments


def _resample(durations, midis, step):
    """Tile each note over its span of grid points of ``step`` quarter
    lengths (round-half-up boundaries, so the tie-break is consistent)."""
    boundaries = np.floor(np.cumsum(durations) / step + 0.5).astype(int)
    counts = np.diff(boundaries, prepend=0)
    return np.repeat(midis, counts)


def _chunk_features(resampled_segments, step, win):
    """Ascent/descent chunk statistics over the smoothed samples of every
    segment (rolling window of 2*win+1 samples, centered)."""
    key_postfix = _motion_postfix(step, win)
    ascending, descending = [], []
    total_steps = 0
    for samples in resampled_segments:
        smoothed_series = pd.Series(samples)
        smoothed = [
            np.mean(window.to_list())
            for window in smoothed_series.rolling(2 * win + 1, center=True)
        ]
        dife = np.diff(smoothed)
        total_steps += len(dife)
        for rising, group in groupby(dife > 0):
            length = sum(1 for _ in group)
            if rising:
                ascending.append(length)
        for falling, group in groupby(dife < 0):
            length = sum(1 for _ in group)
            if falling:
                descending.append(length)
    if total_steps == 0:
        return {
            ASCENDENT_AVERAGE + key_postfix: np.nan,
            DESCENDENT_AVERAGE + key_postfix: np.nan,
            ASCENDENT_PROPORTION + key_postfix: np.nan,
            DESCENDENT_PROPORTION + key_postfix: np.nan,
        }
    return {
        ASCENDENT_AVERAGE + key_postfix: mean(ascending) if ascending else 0,
        DESCENDENT_AVERAGE + key_postfix: mean(descending) if descending else 0,
        ASCENDENT_PROPORTION + key_postfix: sum(ascending) / total_steps
        if ascending
        else 0,
        DESCENDENT_PROPORTION + key_postfix: sum(descending) / total_steps
        if descending
        else 0,
    }


def get_motion_features(part_data) -> dict:
    """Motion features over the part's melodic lines.

    Every line (voice) is resampled separately and split at rests, so the
    time axis is per melodic segment: nothing is measured across
    simultaneous voices or across silences. Speed/acceleration depend only
    on the sampling step; the smoothing window shapes only the chunk
    statistics.
    """
    lines = part_data.get(DATA_MELODIC_LINES)
    if lines is None:
        lines = [part_data["notes_and_rests"]]
    segments = _melodic_segments(lines)

    return_dict = {}
    for step in MOTION_STEPS:
        resampled = [
            _resample(durations, midis, step) for durations, midis in segments
        ]
        resampled = [samples for samples in resampled if samples.size >= 2]

        step_postfix = _motion_step_postfix(step)
        speed_diffs = [np.diff(samples) / step for samples in resampled]
        all_speed = (
            np.concatenate(speed_diffs) if speed_diffs else np.array([])
        )
        return_dict[SPEED_AVG_ABS + step_postfix] = (
            np.mean(np.abs(all_speed)) if all_speed.size else np.nan
        )
        acceleration_diffs = [
            np.diff(diff) / step for diff in speed_diffs if diff.size >= 2
        ]
        all_acceleration = (
            np.concatenate(acceleration_diffs)
            if acceleration_diffs
            else np.array([])
        )
        return_dict[ACCELERATION_AVG_ABS + step_postfix] = (
            np.mean(np.abs(all_acceleration)) if all_acceleration.size else np.nan
        )

        for win in MOTION_WINS:
            return_dict.update(_chunk_features(resampled, step, win))
    return return_dict
