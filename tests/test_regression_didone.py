"""Optional regression against one real DIDONE aria (harmony included).

Runs only when the corpus is available locally (see MUSIF_DIDONE_DIR in
conftest.py); the extraction fixture skips otherwise.
"""
import pandas as pd
import pytest

from tests.conftest import STATIC_DIR
from tests.test_regression import assert_frames_match

EXPECTED = STATIC_DIR / "expected_didone_features.csv"


def test_matches_pinned_baseline(didone_features):
    if not EXPECTED.exists():
        pytest.skip("no pinned DIDONE baseline (run tests/generate_baseline.py)")
    expected = pd.read_csv(EXPECTED, low_memory=False)
    assert_frames_match(didone_features, expected)


def test_relative_degrees_aggregate_all_parts(didone_features):
    row = didone_features.iloc[0]
    assert row["Harmony_Analysis_Available"] == 1
    score_cols = [
        c
        for c in didone_features.columns
        if c.startswith("Score_Degree") and c.endswith("_Count_relative")
    ]
    part_cols = [
        c
        for c in didone_features.columns
        if c.startswith("Part") and "_Degree" in c and c.endswith("_Count_relative")
    ]
    score_total = sum(row[c] for c in score_cols if pd.notna(row[c]))
    part_total = sum(row[c] for c in part_cols if pd.notna(row[c]))
    assert score_total == part_total
    # the original bug made these two columns identical
    assert (
        row["Score_Degree1_Count_relative"]
        != row["PartBs_Degree1_Count_relative"]
    )
    per_cols = [
        c
        for c in didone_features.columns
        if c.startswith("Score_Degree") and c.endswith("_Per_relative")
    ]
    per_sum = sum(row[c] for c in per_cols if pd.notna(row[c]))
    assert abs(per_sum - 1.0) < 1e-9
