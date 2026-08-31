"""Unit tests for the scale / scale_relative degree machinery and the degree
post-processing. These pin the bugs fixed in the 2026-08 audit."""
import pandas as pd
from music21.note import Note
from music21.stream import Measure, Part
from music21.meter import TimeSignature

from musif.extract.constants import DATA_MUSESCORE_SCORE
from musif.extract.features.scale.handler import get_notes_per_degree, to_full_degree
from musif.extract.features.scale_relative.utils import (
    get_emphasised_scale_degrees_relative,
    get_localTonalty,
    get_note_degree,
)
from musif.process.processor import DataProcessor
from musif.process.utils import join_part_degrees


class TestLocalTonality:
    def test_diatonic_and_altered_degrees(self):
        # sharp-spelled tonics used to come back a degree too low
        assert get_localTonalty("A major", "vi") == "f#"
        assert get_localTonalty("B major", "V") == "F#"
        assert get_localTonalty("D major", "iii") == "f#"
        assert get_localTonalty("C major", "bIII") == "E-"
        # flat key + sharp degree used to build the unparseable 'b-#'
        assert get_localTonalty("F major", "#iv") == "b"
        assert get_localTonalty("c minor", "V") == "G"
        assert get_localTonalty("a minor", "bII") == "B-"

    def test_nested_keys_resolve(self):
        # a legal DCML nested key used to wipe the whole relative block
        assert get_localTonalty("C major", "V/V") == "D"

    def test_casing_encodes_mode(self):
        assert get_localTonalty("C major", "V").isupper()
        assert get_localTonalty("C major", "vi").islower()


class TestNoteDegree:
    def test_natural_minor_reference(self):
        # the raised leading tone is #7, the subtonic is 7 (maintainer decision)
        assert get_note_degree("a", "G#") == "#7"
        assert get_note_degree("a", "G") == "7"

    def test_major(self):
        assert get_note_degree("C", "E") == "3"
        assert get_note_degree("C", "E-") == "b3"


class TestScaleCounts:
    def test_all_accidentals_are_counted(self):
        notes = [Note(p) for p in ["C4", "C##4", "C--4", "B#3", "F##4"]]
        counts = get_notes_per_degree("C major", notes)
        # every note counted (double accidentals used to be silently dropped)
        assert sum(counts.values()) == len(notes)
        assert counts["x1"] == 1
        assert counts["bb1"] == 1
        assert counts["x4"] == 1

    def test_unknown_accidental_returns_none(self):
        assert to_full_degree(1, "quadruple-sharp") is None


def _part_notes(measure_pitches, time_signature="4/4"):
    """Build a part and return it together with its notes.

    The part must stay referenced while the notes are used: music21 sites are
    weak references, so measureNumber/beat context dies with the container.
    """
    part = Part()
    for i, pitches in enumerate(measure_pitches, 1):
        measure = Measure(number=i)
        if i == 1:
            measure.append(TimeSignature(time_signature))
        for pitch in pitches:
            measure.append(Note(pitch, quarterLength=1.0))
        part.append(measure)
    notes = [n for m in part.getElementsByClass(Measure) for n in m.notes]
    return part, notes


class TestRelativeDegrees:
    def _harmonic_table(self):
        # C major for measures 1-2, then G major (V) for measures 3-4.
        # Real ms3 tables always carry both mn (written number) and
        # playthrough (unfolded counter); the folded path keys by mn.
        rows = [
            {"mn": 1, "playthrough": 1, "mc_onset": 0, "timesig": "4/4",
             "localkey": "I"},
            {"mn": 3, "playthrough": 3, "mc_onset": 0, "timesig": "4/4",
             "localkey": "V"},
        ]
        return pd.DataFrame(rows)

    def test_notes_follow_the_local_key(self):
        part, notes = _part_notes([["C4"] * 2, ["D4"] * 2, ["G4"] * 2, ["A4"] * 2])
        score_data = {
            DATA_MUSESCORE_SCORE: self._harmonic_table(),
            "key": "C major",
            "file": "synthetic",
        }
        counts = get_emphasised_scale_degrees_relative(notes, score_data)
        # m1-2 in C: C=1, D=2; m3-4 in G: G=1, A=2
        assert counts["1"] == 4
        assert counts["2"] == 4
        assert sum(counts.values()) == 8
        del part

    def test_anacrusis_keys_by_written_measure_number(self):
        # a pickup score numbers its measures 0..3; the local-key map must
        # follow the written numbers, or every key is read one bar late
        # (round-2 R2-8)
        part = Part()
        for number, pitches in enumerate([["C4"], ["C4"], ["G4"], ["G4"]]):
            measure = Measure(number=number)
            if number == 0:
                measure.append(TimeSignature("4/4"))
            for pitch in pitches:
                measure.append(Note(pitch, quarterLength=1.0))
            part.append(measure)
        notes = [n for m in part.getElementsByClass(Measure) for n in m.notes]
        table = pd.DataFrame(
            [
                {"mn": 0, "playthrough": 1, "mc_onset": 0, "timesig": "4/4",
                 "localkey": "I"},
                {"mn": 2, "playthrough": 3, "mc_onset": 0, "timesig": "4/4",
                 "localkey": "V"},
            ]
        )
        score_data = {
            DATA_MUSESCORE_SCORE: table,
            "key": "C major",
            "file": "synthetic",
        }
        counts = get_emphasised_scale_degrees_relative(notes, score_data)
        # mm 0-1: C in C = degree 1; mm 2-3: G in G = degree 1
        assert counts["1"] == 4
        assert sum(counts.values()) == 4
        del part

    def test_no_analysis_returns_none(self):
        part, notes = _part_notes([["C4"]])
        score_data = {
            DATA_MUSESCORE_SCORE: pd.DataFrame(),
            "key": "C major",
            "file": "synthetic",
        }
        assert get_emphasised_scale_degrees_relative(notes, score_data) is None
        del part


class TestDegreeGrouping:
    def _frame(self, prefix):
        return pd.DataFrame(
            {
                f"{prefix}Degree1_Count": [10],
                f"{prefix}Degree1_Per": [0.5],
                f"{prefix}Degree#4_Count": [6],
                f"{prefix}Degree#4_Per": [0.3],
                f"{prefix}Degreeb6_Count": [4],
                f"{prefix}Degreeb6_Per": [0.2],
            }
        )

    def test_counts_and_pers_are_grouped_separately(self):
        df = self._frame("PartVnI_")
        join_part_degrees(list(df.columns), "PartVnI_", df)
        assert df["PartVnI_Degree_Asc_Count"].iloc[0] == 6
        assert df["PartVnI_Degree_Asc_Per"].iloc[0] == 0.3
        assert df["PartVnI_Degree_Nat_Count"].iloc[0] == 10
        assert df["PartVnI_Degree_Nonat_Count"].iloc[0] == 10  # 6 + 4

    def test_prefixes_containing_b_do_not_contaminate(self):
        # 'PartOb_' contains a lowercase b: every column used to land in Desc
        df = self._frame("PartOb_")
        join_part_degrees(list(df.columns), "PartOb_", df)
        assert df["PartOb_Degree_Desc_Count"].iloc[0] == 4  # only the b6
        assert df["PartOb_Degree_Asc_Count"].iloc[0] == 6

    def test_prefix_discovery_includes_score(self):
        columns = [
            "PartVnI_Degree1_Count",
            "Score_Degree1_Count",
            "PartBs_Degree1_Count_relative",
        ]
        prefixes = DataProcessor._degree_prefixes(columns)
        assert "Score_" in prefixes
        assert "PartVnI_" in prefixes
        assert "PartBs_" in prefixes
