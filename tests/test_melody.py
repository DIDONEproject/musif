"""Unit tests for the melody interval and motion features."""
import math

from music21.interval import Interval
from music21.note import Note, Rest
from music21.pitch import Pitch

from musif.extract.features.core.constants import DATA_MELODIC_LINES
from musif.extract.features.melody.handler import (
    get_interval_features,
    get_interval_type_features,
    get_motion_features,
)


def iv(semitones):
    return Interval(semitones)


def note(midi, quarters):
    n = Note()
    n.pitch.midi = midi
    n.duration.quarterLength = quarters
    return n


def rest(quarters):
    r = Rest()
    r.duration.quarterLength = quarters
    return r


def motion(lines):
    return get_motion_features({DATA_MELODIC_LINES: lines})


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
        assert features["SmallestSemitonesDesc"] == -1

    def test_removed_extremes_are_not_emitted(self):
        # Smallest*All degenerates to the unison on any real corpus, and the
        # directional AbsoluteSemitones twins equal the signed versions up to
        # sign: all seven were removed in the round-2 audit
        features = get_interval_features([iv(-12), iv(2)])
        for name in (
            "SmallestSemitonesAll",
            "SmallestIntervalAll",
            "SmallestAbsoluteSemitonesAll",
            "SmallestAbsoluteSemitonesAsc",
            "SmallestAbsoluteSemitonesDesc",
            "LargestAbsoluteSemitonesAsc",
            "LargestAbsoluteSemitonesDesc",
        ):
            assert name not in features


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
        line = [note(60 + i, 0.5) for i in range(20)]
        result = motion([line])
        assert result["Spe_avg_abs_step_1.0"] > 0

    def test_empty_grid_is_nan_not_zero(self):
        line = [note(m, 0.5) for m in (60, 62, 64, 65)]  # 2 quarters total
        result = motion([line])
        assert math.isnan(result["Spe_avg_abs_step_8.0"])

    def test_ascending_proportion_is_bounded(self):
        line = [note(60 + i, 1.0) for i in range(10)]
        result = motion([line])
        assert result["Asc_prp_step_1.0_win_2"] <= 1.0

    def test_speed_names_carry_no_window_suffix(self):
        # the smoothing window never affected Spe/Acc: the _win_ variants
        # were 784 bit-identical duplicate columns (round-2 RD-1)
        result = motion([[note(60 + i, 1.0) for i in range(10)]])
        assert "Spe_avg_abs_step_1.0" in result
        assert "Acc_avg_abs_step_1.0" in result
        assert not any(
            key.startswith(("Spe_avg_abs_step_1.0_win", "Acc_avg_abs_step_1.0_win"))
            for key in result
        )

    def test_rests_split_segments(self):
        # constant pitch on both sides of a rest: measuring across the rest
        # would fabricate a two-octave sweep, split segments measure nothing
        line = [note(48, 4.0), note(48, 4.0), rest(4.0), note(72, 4.0), note(72, 4.0)]
        result = motion([line])
        assert result["Spe_avg_abs_step_1.0"] == 0

    def test_voices_are_never_mixed(self):
        # two simultaneous constant-pitch voices: any cross-voice difference
        # would show up as motion
        soprano = [note(72, 1.0) for _ in range(8)]
        bass = [note(48, 1.0) for _ in range(8)]
        result = motion([soprano, bass])
        assert result["Spe_avg_abs_step_1.0"] == 0
