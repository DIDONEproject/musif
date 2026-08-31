"""Unit tests for the harmony features (built on synthetic ms3-style tables)."""
import pandas as pd

from musif.extract.constants import DATA_MUSESCORE_SCORE
from musif.extract.features.harmony.constants import HARMONY_AVAILABLE
from musif.extract.features.harmony.handler import update_score_objects
from musif.extract.features.harmony.utils import (
    _measure_fraction,
    get_chord_type,
    get_chords,
    get_function_first,
    get_function_second,
    get_harmonic_rhythm,
)
from musif.extract.features.core.constants import FILE_NAME
from musif.extract.features.core.handler import DATA_MODE


class TestHarmonicRhythm:
    def _table(self, measures_per_timesig):
        rows = []
        measure = 1
        for count, timesig in measures_per_timesig:
            for _ in range(count):
                rows.append(
                    {"playthrough": measure, "timesig": timesig, "numeral": "I",
                     "mc_onset": 0}
                )
                rows.append(
                    {"playthrough": measure, "timesig": timesig, "numeral": "V",
                     "mc_onset": 0.5}
                )
                measure += 1
        return pd.DataFrame(rows)

    def test_denominator_covers_all_measures(self):
        table = self._table([(10, "4/4")])
        # 20 chords over 12 measures (2 unannotated trailing measures)
        result = get_harmonic_rhythm(table, number_of_measures=12)
        assert result["Harmony_HarmonicRhythm"] == 20 / 12
        assert result["Harmony_HarmonicRhythmBeats"] == 20 / 48

    def test_metre_changes_count_every_period(self):
        # the final time-signature period used to be dropped entirely
        table = self._table([(20, "4/4"), (100, "3/4")])
        result = get_harmonic_rhythm(table, number_of_measures=120)
        assert abs(result["Harmony_HarmonicRhythmBeats"] - 240 / 380) < 1e-12


class TestRiemannianClassifier:
    def test_vii_family_by_mode(self):
        # the early return used to collapse all of these into 'D'
        assert get_function_first("vii", "m") == "st"
        assert get_function_first("VII", "m") == "ST"
        assert get_function_first("#vii", "m") == "D"
        assert get_function_first("vii", "M") == "D"
        assert get_function_first("#vii", "M") == "#ln"
        assert get_function_first("VII", "M") == "LN"

    def test_second_level_is_none_safe(self):
        assert get_function_second(None) is None


class TestChordNaming:
    def _table(self):
        return pd.DataFrame(
            {
                "relativeroot": [float("nan")] * 4,
                "localkey": ["I"] * 4,
                "chord": ["V7", "#viio", "IVM7", "I"],
                "numeral": ["V", "#vii", "IV", "I"],
                "chord_type": ["Mm7", "o", "MM7", "M"],
            }
        )

    def test_folding_and_seventh_collapse(self):
        chords, _, _ = get_chords(self._table())
        # #viio folds into viio; MM7 collapses to 7
        assert "Harmony_Chord_viio_Count" in chords
        assert not any("#viio" in name for name in chords)
        assert "Harmony_Chord_IV7_Count" in chords
        assert not any("MM7" in name for name in chords)

    def test_chord_types(self):
        assert get_chord_type("M") == "major triad"
        assert get_chord_type("Ger") == "aug6"
        assert get_chord_type("+7") == "aug"


class TestKeyAreaGeometry:
    def test_mc_onset_becomes_a_measure_fraction(self):
        # beat 3 of a 3/4 bar is 2/3 of the measure, not 1/2
        assert abs(_measure_fraction("3/4", 0.5) - 2 / 3) < 1e-12
        assert _measure_fraction("4/4", 0.5) == 0.5


class TestAvailabilityFlag:
    def test_flag_is_zero_when_extraction_fails(self):
        # a table missing most columns makes the extraction blow up mid-way
        broken = pd.DataFrame({"localkey": ["I", "V"]})
        score_features = {FILE_NAME: "broken.xml"}
        update_score_objects(
            {DATA_MUSESCORE_SCORE: broken, DATA_MODE: "major"},
            [], None, [], score_features,
        )
        assert score_features[HARMONY_AVAILABLE] == 0

    def test_flag_is_zero_without_analysis(self):
        score_features = {FILE_NAME: "missing.xml"}
        update_score_objects(
            {DATA_MUSESCORE_SCORE: None, DATA_MODE: "major"},
            [], None, [], score_features,
        )
        assert score_features[HARMONY_AVAILABLE] == 0


def _rows(records):
    return pd.DataFrame(records)


class TestAugmentedSixths:
    def _table(self):
        # chord_type is assigned by ms3 before special labels are expanded,
        # so It/Ger/Fr survive there even though the numeral reads "vii"
        return _rows(
            [
                {"chord": "I", "localkey": "I", "numeral": "I", "chord_type": "M"},
                {"chord": "Ger6", "localkey": "I", "numeral": "vii",
                 "chord_type": "Ger"},
                {"chord": "It6", "localkey": "I", "numeral": "vii",
                 "chord_type": "It"},
                {"chord": "Fr43", "localkey": "I", "numeral": "V",
                 "chord_type": "Fr"},
                {"chord": "V", "localkey": "I", "numeral": "V", "chord_type": "M"},
                {"chord": "I", "localkey": "I", "numeral": "I", "chord_type": "M"},
            ]
        )

    def test_aug6_reaches_its_bucket(self):
        from musif.extract.features.harmony.utils import get_chord_types

        types = get_chord_types(self._table())
        assert types["Harmony_Chord_types_aug6"] == 0.5

    def test_aug6_chords_are_named_not_mangled(self):
        from musif.extract.features.harmony.utils import get_chords

        chords, _, _ = get_chords(self._table())
        count_keys = {key for key in chords if key.endswith("_Count")}
        assert "Harmony_Chord_Ger_Count" in count_keys
        assert "Harmony_Chord_It_Count" in count_keys
        assert "Harmony_Chord_Fr_Count" in count_keys
        assert not any("viiIt" in key or "viiGer" in key for key in count_keys)


class TestNonHarmonyRows:
    def test_at_none_is_not_a_chord(self):
        table = _rows(
            [
                {"chord": "I", "localkey": "I", "numeral": "I", "chord_type": "M",
                 "playthrough": 1, "timesig": "4/4", "mc_onset": 0},
                {"chord": "@none", "localkey": "I", "numeral": "@none",
                 "chord_type": "m", "playthrough": 2, "timesig": "4/4",
                 "mc_onset": 0},
                {"chord": "V", "localkey": "I", "numeral": "V", "chord_type": "M",
                 "playthrough": 3, "timesig": "4/4", "mc_onset": 0},
                {"chord": "I", "localkey": "I", "numeral": "I", "chord_type": "M",
                 "playthrough": 4, "timesig": "4/4", "mc_onset": 0},
            ]
        )
        assert get_harmonic_rhythm(table, 4)["Harmony_HarmonicRhythm"] == 0.75


class TestLocalKeyMode:
    def test_flat_major_keys_classify_as_major(self):
        # DCML: minor iff the numeral is all-lowercase; bVI is a MAJOR key
        from musif.extract.features.harmony.utils import get_first_chord_local

        assert get_first_chord_local("viio", "bVI") == "D"
        assert get_first_chord_local("viio", "vi") == "st"


class TestKeyAreasPlaythrough:
    def test_mid_measure_change_is_onset_aware(self):
        from musif.extract.features.harmony.utils import get_keyareas

        table = _rows(
            [
                {"localkey": "I", "playthrough": 1, "mc_onset": 0,
                 "timesig": "3/4"},
                {"localkey": "I", "playthrough": 2, "mc_onset": 0,
                 "timesig": "3/4"},
                {"localkey": "V", "playthrough": 3, "mc_onset": 0.25,
                 "timesig": "3/4"},
                {"localkey": "V", "playthrough": 4, "mc_onset": 0,
                 "timesig": "3/4"},
            ]
        )
        areas = get_keyareas(table)
        # I holds mm 1-2 plus the first third of m 3 (0.25 of a whole note
        # in 3/4): (2 + 1/3) / 4
        assert abs(areas["Harmony_Key_I_PercentageMeasures"] - (2 + 1 / 3) / 4) < 1e-9

    def test_unfolded_repeats_follow_playthrough(self):
        from musif.extract.features.harmony.utils import get_keyareas

        rows = [
            {"localkey": "I" if playthrough <= 4 else "V",
             "playthrough": playthrough, "mc_onset": 0, "timesig": "4/4"}
            for playthrough in range(1, 9)
        ]
        areas = get_keyareas(_rows(rows))
        assert areas["Harmony_Key_I_PercentageMeasures"] == 0.5
        assert areas["Harmony_Key_V_PercentageMeasures"] == 0.5
