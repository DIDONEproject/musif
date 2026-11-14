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


def test_unfolded_aria_follows_the_reprise(didone_features, didone_unfolded_features):
    written = didone_features.iloc[0]
    unfolded = didone_unfolded_features.iloc[0]
    assert written["RepeatsUnfolded"] == 0
    assert unfolded["RepeatsUnfolded"] == 1
    assert written["RepriseInstruction"] == unfolded["RepriseInstruction"] == 1
    # bars 1-59, from the segno (bar 14) to the coda sign (bar 43), and the
    # coda (bar 60): the order ms3 gives the MuseScore file
    assert written["Measures"] == 60
    assert unfolded["Measures"] == 59 + 30 + 1
    assert unfolded["Score_Notes"] > written["Score_Notes"]
    # the labels follow the measures: every note has a local key
    relative = [
        c for c in didone_unfolded_features.columns
        if c.startswith("Score_Degree") and c.endswith("_Count_relative")
    ]
    assert sum(unfolded[c] for c in relative if pd.notna(unfolded[c])) == unfolded["Score_Notes"]
    assert unfolded["Harmony_Analysis_Available"] == 1


def test_reading_a_musescore_file_keeps_nothing_in_memory():
    # ms3 caches methods of its parser at class level: every file read used to
    # stay in memory with its whole parse tree (about 40 MB a score), and a run
    # of the corpus filled the swap
    import gc

    from tests.conftest import DIDONE_DIR, DIDONE_SAMPLE
    from musif.extract.utils import performance_order, process_musescore_file

    mscx = DIDONE_DIR / "musescore" / f"{DIDONE_SAMPLE}.mscx"
    if not mscx.exists():
        pytest.skip(f"DIDONE corpus not available at {DIDONE_DIR}")
    process_musescore_file(str(mscx))
    process_musescore_file(str(mscx), expand_repeats=True)
    performance_order(str(mscx))
    gc.collect()
    parsers = [o for o in gc.get_objects() if type(o).__name__ == "_MSCX_bs4"]
    assert parsers == []
