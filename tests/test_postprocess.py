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


class TestGroupedAnalysis:
    def test_degree_groups_for_every_present_prefix(self):
        data = _process(_frame(), grouped_analysis=True)
        assert "Score_Degree_Nat_Count" in data.columns
        assert "PartVnI_Degree_Nat_Count" in data.columns
        assert data["Score_Degree_Nat_Count"].tolist() == [20, 16]

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
