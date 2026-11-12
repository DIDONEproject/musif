"""Unit tests for the dynamics features."""
import math

from music21.dynamics import Dynamic
from music21.meter import TimeSignature
from music21.note import Note, Rest
from music21.stream import Measure

from musif.extract.constants import DATA_PART_ABBREVIATION, GLOBAL_TIME_SIGNATURE
from musif.extract.features.core.constants import DATA_SOUNDING_MEASURES
from musif.extract.features.dynamics.handler import (
    update_part_objects,
    update_score_objects,
)

SCORE_DATA = {GLOBAL_TIME_SIGNATURE: TimeSignature("4/4"), "file": "synthetic"}


def _part(abbreviation, marking=None):
    """Four 4/4 measures, the first silent and the others sounding; `marking`,
    if given, opens the second measure."""
    measures = []
    for index in range(4):
        measure = Measure(number=index + 1)
        if index == 0:
            measure.append(Rest(quarterLength=4))
        else:
            if marking and index == 1:
                measure.insert(0, Dynamic(marking))
            measure.append(Note("C5", quarterLength=4))
        measures.append(measure)
    part_data = {
        "measures": measures,
        DATA_SOUNDING_MEASURES: [1, 2, 3],
        DATA_PART_ABBREVIATION: abbreviation,
    }
    part_features = {}
    update_part_objects(SCORE_DATA, part_data, None, part_features)
    return part_data, part_features


class TestPartsWithoutMarkings:
    def test_part_features_are_nan_not_zero(self):
        # the level of 0 inserted by the silent measure used to pass for a
        # marking, so the part reported a mean dynamic of 0
        _, features = _part("sop")
        assert math.isnan(features["DynMean"])
        assert math.isnan(features["DynMean_weighted"])
        assert math.isnan(features["DynGrad"])

    def test_they_stay_out_of_the_score_means(self):
        marked_data, marked = _part("vnI", "f")
        unmarked_data, unmarked = _part("sop")
        score_features = {}
        update_score_objects(
            SCORE_DATA,
            [marked_data, unmarked_data],
            None,
            [marked, unmarked],
            score_features,
        )
        assert math.isnan(score_features["PartSop_DynMean"])
        assert score_features["Score_DynMean"] == marked["DynMean"]
        assert score_features["Score_DynMean_weighted"] == marked["DynMean_weighted"]

    def test_score_is_nan_when_no_part_has_markings(self):
        data, features = _part("sop")
        score_features = {}
        update_score_objects(SCORE_DATA, [data], None, [features], score_features)
        assert math.isnan(score_features["Score_DynMean"])
        assert math.isnan(score_features["Score_DynMean_weighted"])


class TestSilenceIsNotALevel:
    def test_silent_measure_adds_no_level(self):
        # a silent measure used to insert a level of 0, which weighed in the
        # mean as much as the forte
        _, features = _part("vnI", "f")
        assert features["DynMean"] == 88
        assert features["DynMean_weighted"] == 88

    def _part_with_a_silence(self, time_signature="4/4"):
        """f in the first measure, a silent second measure, a third measure
        without a new marking, and p in the fourth."""
        score_data = {
            GLOBAL_TIME_SIGNATURE: TimeSignature(time_signature),
            "file": "synthetic",
        }
        measures = []
        for index in range(4):
            measure = Measure(number=index + 1)
            if index == 0:
                measure.insert(0, Dynamic("f"))
            if index == 3:
                measure.insert(0, Dynamic("p"))
            measure.append(Rest(quarterLength=4) if index == 1 else Note("C5", quarterLength=4))
            measures.append(measure)
        part_data = {
            "measures": measures,
            DATA_SOUNDING_MEASURES: [0, 2, 3],
            DATA_PART_ABBREVIATION: "ob",
        }
        features = {}
        update_part_objects(score_data, part_data, None, features)
        return features

    def test_marking_stays_in_force_through_a_rest(self):
        features = self._part_with_a_silence()
        # two levels, forte and piano: the silence is not a third one
        assert features["DynMean"] == (88 + 49) / 2
        # forte sounds for two measures (the first and the third), piano for one
        assert features["DynMean_weighted"] == (88 * 8 + 49 * 4) / 12

    def test_gradient_spans_the_real_time_between_markings(self):
        features = self._part_with_a_silence()
        # from f to p over three measures of 4/4
        assert features["DynGrad"] == (88 - 49) / 12
        assert features["DynGradQuarters"] == (88 - 49) / 12

    def test_per_quarter_rates_do_not_follow_the_beat_unit(self):
        # the same notes under 2/2: two beats per measure, still four quarters
        features = self._part_with_a_silence("2/2")
        assert features["DynGrad"] == (88 - 49) / 6
        assert features["DynGradQuarters"] == (88 - 49) / 12
        assert features["DynAbruptness"] == (88 - 49) / 6 / 8
        assert features["DynAbruptnessQuarters"] == (88 - 49) / 12 / 16

    def test_what_sounds_before_the_first_marking_has_no_level(self):
        # three sounding measures, the marking opens the second of them... the
        # helper's part rests in the first measure, so shift the marking
        data, _ = _part("vnI")
        data["measures"][2].insert(0, Dynamic("p"))
        features = {}
        update_part_objects(SCORE_DATA, data, None, features)
        # one unmarked sounding measure is left out of the weighted mean
        assert features["DynMean_weighted"] == 49
