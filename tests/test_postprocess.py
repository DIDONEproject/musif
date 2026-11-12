"""Unit tests for DataProcessor post-processing behavior."""
import numpy as np
import pandas as pd

from musif.process.processor import DataProcessor
from musif.process.utils import join_keys


def _frame():
    return pd.DataFrame(
        {
            "Id": [0, 1],
            "WindowId": [0, 0],
            "FileName": ["a.xml", "b.xml"],
            "Instrumentation": ["vn,bs", "ob,bs"],
            "SoundVn_Notes": [100, 90],
            "FamilyInstrumentation": ["str", "str"],
            "FamilyScoring": ["str,voice", "str,voice"],
            "PartVnI_Degree1_Count": [10, 8],
            "PartVnI_Degree1_Per": [1.0, 1.0],
            "Score_Degree1_Count": [20, 16],
            "Score_Degree1_Per": [1.0, 1.0],
            "MostlyNaN": [np.nan, 1.0],
        }
    )


def _process(df, **overrides):
    config = {"max_nan_rows": 1.0}
    config.update(overrides)
    return DataProcessor(df, config).process().data


class TestColumnDeletion:
    def test_sound_and_family_columns_survive_by_default(self):
        data = _process(_frame())
        assert "SoundVn_Notes" in data.columns
        assert "FamilyInstrumentation" in data.columns

    def test_delete_sound_columns_option(self):
        data = _process(_frame(), delete_sound_columns=True)
        assert "SoundVn_Notes" not in data.columns
        assert "FamilyInstrumentation" not in data.columns

    def test_null_max_nan_columns_keeps_everything(self):
        data = _process(_frame())
        assert "MostlyNaN" in data.columns

    def test_max_nan_columns_threshold(self):
        data = _process(_frame(), max_nan_columns=0.0)
        assert "MostlyNaN" not in data.columns


REPLACE = ["Interval", "Degree", "Harmony"]


class TestNanReplacement:
    """An empty cell becomes 0 only where 0 is the measured value: an event
    that did not happen in a part that plays."""

    def _frame(self):
        nan = np.nan
        return pd.DataFrame(
            {
                "Id": [0, 1, 2, 3],
                "WindowId": [0, 0, 0, 0],
                "FileName": ["a.xml", "b.xml", "c.xml", "d.xml"],
                # the soprano sings in every score but the third
                "PartSop_Notes": [100, 120, nan, 90],
                "PartSop_IntervalM3_Per": [0.2, nan, nan, 0.5],
                "PartSop_IntervalA5_Per": [nan, nan, nan, 0.01],
                "PartSop_IntervallicTrimRatio": [0.1, nan, nan, 0.3],
                "PartSop_Degree1_Per_relative": [0.3, nan, nan, nan],
                # the fourth score has no harmonic analysis
                "Harmony_Analysis_Available": [1, 1, 1, 0],
                "Harmony_Chord_Ger_Per": [0.1, nan, nan, nan],
                "Harmony_HarmonicRhythm": [1.5, 2.0, 1.0, nan],
                # a flute plays in the fourth score only
                "PartFl_Notes": [nan, nan, nan, 50],
                "PartFl_IntervalM3_Per": [nan, nan, nan, 0.5],
                "PartFl_Ambitus": [nan, nan, nan, 12.0],
            }
        )

    def _column(self, name, df=None, **overrides):
        df = self._frame() if df is None else df
        data = _process(df, replace_nans=REPLACE, **overrides)
        return data.sort_values("Id")[name].tolist()

    def test_event_that_did_not_happen_is_zero(self):
        # second score: the soprano sings, without a single major third
        assert self._column("PartSop_IntervalM3_Per")[1] == 0.0

    def test_absent_part_stays_empty(self):
        # third score: there is no soprano, so there is nothing to measure;
        # a 0 there would read as a soprano who never sings a major third
        assert np.isnan(self._column("PartSop_IntervalM3_Per")[2])

    def test_statistics_are_never_replaced(self):
        # "Interval" selects this column too, but a ratio that could not be
        # computed does not become 0 (it is NaN by definition when the mean
        # interval is 0)
        values = self._column("PartSop_IntervallicTrimRatio")
        assert np.isnan(values[1]) and np.isnan(values[2])

    def test_relative_degrees_need_the_part_and_the_analysis(self):
        values = self._column("PartSop_Degree1_Per_relative")
        assert values[1] == 0.0  # soprano and analysis: a measured zero
        assert np.isnan(values[2])  # no soprano
        assert np.isnan(values[3])  # soprano, but no harmonic analysis

    def test_harmony_columns_need_the_analysis(self):
        values = self._column("Harmony_Chord_Ger_Per")
        assert values[1] == 0.0 and values[2] == 0.0
        assert np.isnan(values[3])
        assert np.isnan(self._column("Harmony_HarmonicRhythm")[3])

    def test_threshold_drops_the_parts_few_scores_have(self):
        # the flute is absent from 75% of the scores: its cells stay empty,
        # so max_nan_columns deletes all its columns alike. Replacing every
        # NaN first used to keep its interval columns, as zeros, and delete
        # only the rest of the part
        data = _process(self._frame(), replace_nans=REPLACE, max_nan_columns=0.7)
        assert not [c for c in data.columns if c.startswith("PartFl_")]

    def test_rare_event_of_a_common_part_survives_the_threshold(self):
        # an augmented fifth occurs in one score, yet the column is empty only
        # where the soprano is absent (25%): elsewhere it holds measured zeros
        values = self._column("PartSop_IntervalA5_Per", max_nan_columns=0.7)
        assert values[:2] == [0.0, 0.0] and np.isnan(values[2])

    def test_note_counts_may_be_deleted_by_the_configuration(self):
        # presence is read before the deletions take the note counts away
        data = _process(
            self._frame(), replace_nans=REPLACE, columns_endswith=["_Notes"]
        ).sort_values("Id")
        assert "PartSop_Notes" not in data.columns
        values = data["PartSop_IntervalM3_Per"].tolist()
        assert values[1] == 0.0 and np.isnan(values[2])

    def test_without_note_counts_presence_is_read_from_the_part_columns(self):
        frame = self._frame().drop(columns=["PartSop_Notes", "PartFl_Notes"])
        values = self._column("PartSop_IntervalA5_Per", df=frame)
        # the soprano has values in the first, second (none) ... scores:
        # present wherever any of its columns holds one
        assert values[0] == 0.0 and np.isnan(values[2])

    def test_part_without_notes_has_no_proportions(self):
        frame = self._frame()
        frame.loc[1, "PartSop_Notes"] = 0  # a staff that never plays
        assert np.isnan(self._column("PartSop_IntervalM3_Per", df=frame)[1])


class TestInstrumentationSeparation:
    def test_presence_columns_align_after_row_deletion(self):
        df = _frame().drop(index=0)  # a non-contiguous index used to corrupt this
        data = _process(df, separate_instrumentation_column=True)
        assert len(data) == 1  # positional .at[] used to append phantom rows
        row = data.iloc[0]
        assert row["Presence_of_ob"] == 1
        assert row["Presence_of_bs"] == 1
        # vn only appeared in the deleted row, so no column is created for it
        assert "Presence_of_vn" not in data.columns


class TestFailedScore:
    def test_presence_stays_empty_without_an_instrumentation(self):
        # a score that failed to extract has no list of instruments: a 0
        # would say that it has no violins
        frame = _frame()
        frame.loc[1, "Instrumentation"] = np.nan
        data = _process(frame, separate_instrumentation_column=True).sort_values("Id")
        assert data["Presence_of_vn"].iloc[0] == 1
        assert data["Presence_of_bs"].iloc[0] == 1
        assert np.isnan(data["Presence_of_vn"].iloc[1])


class TestGroupedAnalysis:
    def test_degree_groups_for_every_present_prefix(self):
        data = _process(_frame(), grouped_analysis=True)
        assert "Score_Degree_Nat_Count" in data.columns
        assert "PartVnI_Degree_Nat_Count" in data.columns
        assert data["Score_Degree_Nat_Count"].tolist() == [20, 16]

    def test_degree_groups_stay_empty_for_an_absent_part(self):
        frame = _frame()
        frame["PartOb_Degree1_Count"] = [np.nan, 12]
        frame["PartOb_Degree1_Per"] = [np.nan, 1.0]
        data = _process(frame, grouped_analysis=True).sort_values("Id")
        assert np.isnan(data["PartOb_Degree_Nat_Count"].iloc[0])
        assert data["PartOb_Degree_Nat_Count"].iloc[1] == 12
        # a group without any column of its kind is 0 only where the part is
        assert np.isnan(data["PartOb_Degree_Asc_Count"].iloc[0])
        assert data["PartOb_Degree_Asc_Count"].iloc[1] == 0

    def test_key_groups_stay_empty_without_analysis(self):
        frame = _frame()
        frame["Harmony_Key_I_PercentageMeasures"] = [np.nan, 0.7]
        frame["Harmony_Key_V_PercentageMeasures"] = [np.nan, 0.3]
        data = _process(frame, grouped_analysis=True).sort_values("Id")
        assert np.isnan(data["Harmony_Key_T_PercentageMeasures"].iloc[0])
        assert data["Harmony_Key_T_PercentageMeasures"].iloc[1] == 0.7
        assert data["Harmony_Key_sd_PercentageMeasures"].iloc[1] == 0.0

    def test_key_grouping_has_dominant_buckets(self):
        df = pd.DataFrame(
            {
                "Harmony_Key_I_PercentageMeasures": [0.5],
                "Harmony_Key_V_PercentageMeasures": [0.3],
                "Harmony_Key_vi_PercentageMeasures": [0.2],
            }
        )
        join_keys(df)
        assert df["Harmony_Key_D_PercentageMeasures"].iloc[0] == 0.3
        assert df["Harmony_Key_Dom_PercentageMeasures"].iloc[0] == 0.3
        assert df["Harmony_Key_T_PercentageMeasures"].iloc[0] == 0.5
        # V no longer leaks into Other
        assert df["Harmony_Key_Other_PercentageMeasures"].iloc[0] == 0.0


class TestKeyGroupingIdempotency:
    def test_join_keys_twice_gives_same_result(self):
        # the derived buckets must be excluded from "Other", or re-processing
        # an already-processed frame inflates it (round-2 O3-8)
        import pandas as pd

        from musif.extract.features.harmony.constants import (
            KEY_PERCENTAGE,
            KEY_PREFIX,
        )
        from musif.process.utils import join_keys

        frame = pd.DataFrame(
            {
                KEY_PREFIX + "I" + KEY_PERCENTAGE: [0.5],
                KEY_PREFIX + "V" + KEY_PERCENTAGE: [0.3],
                KEY_PREFIX + "bVII" + KEY_PERCENTAGE: [0.2],
            }
        )
        join_keys(frame)
        first = frame.copy()
        join_keys(frame)
        pd.testing.assert_frame_equal(frame, first)
