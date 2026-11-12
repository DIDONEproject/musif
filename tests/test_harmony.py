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


NAN = float("nan")


def _chord(chord, numeral, chord_type, duration, figbass=NAN, relativeroot=NAN,
           localkey="I", special=NAN, changes=NAN):
    return {
        "chord": chord, "localkey": localkey, "numeral": numeral,
        "chord_type": chord_type, "figbass": figbass,
        "relativeroot": relativeroot, "duration_qb": duration,
        "special": special, "changes": changes,
    }


class TestWhatIsCounted:
    """Chords on the degrees of the key, applied chords and augmented sixths
    are counted apart; every proportion exists by annotations and by time."""

    def _table(self):
        # eight chords over ten quarter notes
        return _rows(
            [
                _chord("I", "I", "M", 4.0),
                _chord("V7/V", "V", "Mm7", 1.0, figbass="7", relativeroot="V"),
                _chord("V7", "V", "Mm7", 1.0, figbass="7"),
                _chord("Ger65", "vii", "Ger", 1.0, figbass="65", relativeroot="V",
                       special="Ger", changes="b3"),
                _chord("I64", "I", "M", 0.5, figbass="64"),
                _chord("V(64)", "V", "M", 0.5, changes="64"),
                _chord("vi", "vi", "m", 1.0),
                _chord("I", "I", "M", 1.0),
            ]
        )

    def test_applied_chord_is_not_a_chord_of_the_key(self):
        # V7/V used to be counted as the V7 of the key
        chords, _, _ = get_chords(self._table())
        assert chords["Harmony_Chord_V7_Count"] == 1
        assert chords["Harmony_Applied_V7_Count"] == 1
        # both proportions share one denominator: all the chords
        assert chords["Harmony_Chord_V7_Per"] == 1 / 8
        assert chords["Harmony_Applied_V7_Per"] == 1 / 8

    def test_numerals_of_the_key_only(self):
        from musif.extract.features.harmony.utils import get_numerals

        numerals = get_numerals(self._table())
        assert numerals["Harmony_Numerals_V_Count"] == 2  # V7 and V
        assert numerals["Harmony_Numerals_Applied_Count"] == 1
        # ms3 spells the German sixth as a vii applied to V
        assert numerals["Harmony_Numerals_Aug6_Count"] == 1
        assert "Harmony_Numerals_vii_Count" not in numerals

    def test_proportion_of_time(self):
        chords, _, _ = get_chords(self._table())
        # the tonic is 3 of 8 annotations but 5.5 of 10 quarter notes
        assert chords["Harmony_Chord_I_Per"] == 3 / 8
        assert chords["Harmony_Chord_I_PerTime"] == 5.5 / 10

    def test_chord_types_by_time(self):
        from musif.extract.features.harmony.utils import get_chord_types

        types = get_chord_types(self._table())
        assert types["Harmony_Chord_types_7th"] == 2 / 8
        assert types["Harmony_Chord_types_7th_PerTime"] == 2 / 10

    def test_functions(self):
        _, first, second = get_chords(self._table())
        prefix = "Harmony_Chords_Grouping_"
        # the two tonics and the I64: a six-four annotated on I is a tonic,
        # even when a dominant follows
        assert first[prefix + "1T_Count"] == 3
        # V7 and the cadential six-four, which is the one annotated V(64)
        assert first[prefix + "1D_Count"] == 2
        assert first[prefix + "1SEC_Count"] == 1  # the applied chord
        assert first[prefix + "1A6_Count"] == 1  # the augmented sixth
        assert first[prefix + "1rm_Count"] == 1  # vi, the relative minor
        assert second[prefix + "2rel_Count"] == 1
        assert second[prefix + "2D_PerTime"] == (1.0 + 0.5) / 10

    def test_relative_of_a_minor_key(self):
        assert get_function_first("III", "m") == "rj"
        assert get_function_first("vi", "M") == "rm"
        assert get_function_second("rj") == "rel"
        # the same numerals in the other mode are not the relative
        assert get_function_first("vi", "m") != "rm"

    def test_alteration_of_an_augmented_sixth_is_not_an_addition(self):
        from musif.extract.features.harmony.utils import get_additions

        additions = get_additions(self._table())
        # the b3 that ms3 writes for the German sixth used to fall in the
        # "other alterations" bucket
        assert "Harmony_Additions_Others_no_+" not in additions
        # the (64) of the cadential six-four
        assert additions["Harmony_Additions_4_6_64"] == 1 / 8

    def test_harmonic_rhythm_per_quarter_note(self):
        rows = []
        for measure in range(1, 11):
            for onset in (0, 0.5):
                rows.append({"playthrough": measure, "timesig": "3/8",
                             "numeral": "I", "mc_onset": onset})
        result = get_harmonic_rhythm(pd.DataFrame(rows), number_of_measures=10)
        # one beat per measure of 3/8, but a quarter note and a half
        assert result["Harmony_HarmonicRhythmBeats"] == 20 / 10
        assert result["Harmony_HarmonicRhythmQuarters"] == 20 / 15
