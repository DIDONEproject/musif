"""Regression tests: the extracted DataFrame must match the pinned baseline.

If a legitimate change alters extraction output, regenerate the baseline with
``python tests/generate_baseline.py`` and review the diff.
"""
import numpy as np
import pandas as pd

_POISON = -9.87654321e15


def _sorted_by_filename(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values("FileName").reset_index(drop=True)


def assert_frames_match(actual: pd.DataFrame, expected: pd.DataFrame):
    actual = _sorted_by_filename(actual)
    expected = _sorted_by_filename(expected)

    missing = sorted(set(expected.columns) - set(actual.columns))
    unexpected = sorted(set(actual.columns) - set(expected.columns))
    assert not missing, f"columns missing from extraction: {missing[:20]}"
    assert not unexpected, f"columns not in the baseline: {unexpected[:20]}"

    mismatched = []
    for column in expected.columns:
        a = actual[column]
        e = expected[column]
        a_num = pd.to_numeric(a, errors="coerce").astype(float)
        e_num = pd.to_numeric(e, errors="coerce").astype(float)
        numeric_ok = np.isclose(
            a_num.fillna(_POISON), e_num.fillna(_POISON), rtol=1e-6, atol=1e-9
        )
        # where the baseline is non-numeric (strings, 'NA' sentinels, NaN),
        # fall back to string comparison
        text_mask = e_num.isna() & a_num.isna()
        text_ok = a.astype(str).values == e.astype(str).values
        if not np.all(numeric_ok | (text_mask.values & text_ok)):
            mismatched.append(column)
    assert not mismatched, (
        f"{len(mismatched)} columns differ from the baseline, e.g. "
        f"{mismatched[:15]}"
    )


def test_columns_and_values_match_baseline(extracted_features, expected_features):
    assert_frames_match(extracted_features, expected_features)


def test_artist_and_title_from_filename(extracted_features):
    df = _sorted_by_filename(extracted_features)
    synthetic = df[df.FileName == "TestComposer_synthetic_piece.xml"].iloc[0]
    assert synthetic["Artist"] == "TestComposer"
    assert synthetic["Title"] == "synthetic_piece"
    example = df[df.FileName == "example.xml"].iloc[0]
    assert str(example["Artist"]) in ("", "nan")
    assert example["Title"] == "example"


def test_degree_invariants(extracted_features):
    """Score-level degrees aggregate ALL parts; percentages sum to 1."""
    df = extracted_features
    for _, row in df.iterrows():
        count_cols = [
            c
            for c in df.columns
            if c.startswith("Score_Degree") and c.endswith("_Count")
        ]
        per_cols = [
            c for c in df.columns if c.startswith("Score_Degree") and c.endswith("_Per")
        ]
        score_total = sum(row[c] for c in count_cols if pd.notna(row[c]))
        part_total = sum(
            row[c]
            for c in df.columns
            if c.startswith("Part") and "_Degree" in c and c.endswith("_Count")
            and pd.notna(row[c])
        )
        assert score_total == part_total
        assert score_total == row["Score_Notes"]
        per_sum = sum(row[c] for c in per_cols if pd.notna(row[c]))
        assert abs(per_sum - 1.0) < 1e-9


def test_largest_interval_invariants(extracted_features):
    """The 'All' extreme is the largest magnitude in either direction."""
    df = extracted_features
    for column in df.columns:
        if not column.endswith("LargestAbsoluteSemitonesAll"):
            continue
        for direction in ("Asc", "Desc"):
            other = column.replace("All", direction)
            if other not in df.columns:
                continue
            for _, row in df.iterrows():
                if pd.notna(row[column]) and pd.notna(row[other]):
                    assert row[column] >= row[other], (column, other)


def test_synthetic_score_spot_values(extracted_features):
    """Hand-checked values of the synthetic score, independent of the CSV."""
    row = extracted_features[
        extracted_features.FileName == "TestComposer_synthetic_piece.xml"
    ].iloc[0]
    # violin: 24 notes, one silent measure (m3)
    assert row["PartVnI_Notes"] == 24
    assert row["PartVnI_SoundingMeasures"] == 7
    assert row["Measures"] == 8
    # C5->C5 in m4 and across the m7|m8 barline: two true repeats; the
    # chromatic unisons C5->C#5->C5 count as stepwise motion instead
    assert row["PartVnI_RepeatedNotes_Count"] == 2
    # the largest leap is descending (C6->C4 = 24 semitones)
    assert row["PartVnI_LargestAbsoluteSemitonesAll"] == 24
    assert row["PartVnI_LargestSemitonesAll"] == -24
    assert row["PartVnI_LargestIntervalAll"] == "P-15"
    # one dotted figure (m2: dotted eighth + sixteenth)
    # sounding beats: m1,2 = 4+4, m4,5,6 = 12, m7,8 = 3+3 -> 26
    assert row["PartVnI_DottedRhythm"] == 1 / 26
    # metre change is preserved for density but TimeSignature is the initial one
    assert row["TimeSignature"] == "4/4"
    # ambitus at all scopes
    assert row["Score_Ambitus"] == row["Score_HighestNoteIndex"] - row["Score_LowestNoteIndex"]
    assert row["SoundVc_LowestNote"] == "C2"
    # lyrics: soprano has 10 syllables (one per lyric token)
    assert row["PartSop_Syllables"] == 10
    # texture pair uses true note counts (violin 24, cello 13) and the
    # canonical scoring order puts vnI before vc
    assert abs(row["PartVnI|PartVc_Texture"] - 24 / 13) < 1e-9
