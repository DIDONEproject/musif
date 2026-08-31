"""Unit tests for the melody interval and motion features."""
import math

import numpy as np
from music21.interval import Interval
from music21.note import Note
from music21.pitch import Pitch

from musif.extract.features.melody.handler import (
    _motion_features_single_window_step,
    get_interval_features,
    get_interval_type_features,
)


def iv(semitones):
    return Interval(semitones)


class TestExtremes:
    def test_largest_all_is_selected_by_magnitude(self):
        features = get_interval_features([iv(-12), iv(2)])
        assert features["LargestSemitonesAll"] == -12
        assert features["LargestAbsoluteSemitonesAll"] == 12
        assert features["LargestIntervalAll"] == "P-8"

    def test_notated_spelling_is_preserved(self):
        tritone = Interval(Pitch("C4"), Pitch("F#4"))  # an A4, 6 semitones
        features = get_interval_features([tritone])
        assert features["LargestIntervalAll"] == "A4"  # not the re-derived d5

    def test_all_descending_part(self):
        features = get_interval_features([iv(-12), iv(-1)])
        assert features["LargestSemitonesAll"] == -12
        assert features["SmallestSemitonesAll"] == -1


class TestStatSentinels:
    def test_trim_ratio_is_nan_when_mean_is_zero(self):
        features = get_interval_features([iv(3), iv(-3)])
        assert math.isnan(features["IntervallicTrimRatio"])

    def test_empty_scope_yields_undefined_stats(self):
        features = get_interval_features([])
        assert features["MeanInterval"] is None
        assert math.isnan(features["IntervallicMean"])
        assert features["LargestIntervalAll"] is None


class TestClassification:
    def test_chromatic_unisons_are_stepwise_not_repeats(self):
        notes = [Note("C4"), Note("C#4"), Note("C4"), Note("C4")]
        intervals = [
            Interval(notes[i], notes[i + 1]) for i in range(len(notes) - 1)
        ]
        features = get_interval_type_features(intervals)
        assert features["RepeatedNotes_Count"] == 1
        assert features["StepwiseMotionAll_Count"] == 2


class TestMotion:
    def test_short_notes_are_not_dropped(self):
        # 20 eighth notes at step=1.0: the old sampler dropped every note
        durations = np.array([0.5] * 20)
        midis = np.array(range(60, 80))
        result = _motion_features_single_window_step(durations, midis, 1.0, 2)
        assert result["Spe_avg_abs_step_1.0_win_2"] > 0

    def test_empty_grid_is_nan_not_zero(self):
        durations = np.array([0.5] * 4)  # 2 quarters total, step 8.0
        midis = np.array([60, 62, 64, 65])
        result = _motion_features_single_window_step(durations, midis, 8.0, 2)
        assert math.isnan(result["Spe_avg_abs_step_8.0_win_2"])

    def test_ascending_proportion_is_bounded(self):
        durations = np.array([1.0] * 10)
        midis = np.array(range(60, 70))
        result = _motion_features_single_window_step(durations, midis, 1.0, 2)
        assert result["Asc_prp_step_1.0_win_2"] <= 1.0
