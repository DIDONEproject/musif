"""Unit tests for the rhythm and tempo features."""
from music21.meter import TimeSignature
from music21.note import Note
from music21.stream import Measure, Part

from musif.extract.features.core.constants import DATA_SOUNDING_MEASURES
from musif.extract.features.rhythm.handler import update_part_objects
from musif.musicxml.tempo import (
    get_number_of_beats,
    get_tempo_grouped_1,
    get_tempo_grouped_2,
    get_time_signature_type,
)


class TestTempoGrouping:
    def test_na_maps_to_na_not_none(self):
        assert get_tempo_grouped_2("NA") == "NA"

    def test_unknown_terms_map_to_na(self):
        assert get_tempo_grouped_2("Zanzara") == "NA"

    def test_brio_normalization(self):
        assert get_tempo_grouped_1("brio e tempo") == "Con brio"
        assert get_tempo_grouped_2("Con brio") == "Fast"

    def test_common_terms(self):
        assert get_tempo_grouped_2("Adagio") == "Slow"
        assert get_tempo_grouped_2("Andante") == "Moderate"
        assert get_tempo_grouped_2("Allegro") == "Fast"


class TestTimeSignatures:
    def test_six_x_metres_are_compound_duple(self):
        for time_signature in ("6/8", "6/4", "6/2", "6/16"):
            assert get_time_signature_type(time_signature) == "compound duple"

    def test_simple_triple(self):
        assert get_time_signature_type("3/4") == "simple triple"

    def test_number_of_beats(self):
        assert get_number_of_beats("4/4") == 4
        assert get_number_of_beats("6/8") == 2
        assert get_number_of_beats("3/8") == 1
        assert get_number_of_beats("C") == 4


class TestRhythmFormulas:
    def _part_data(self):
        part = Part()
        m1 = Measure(number=1)
        m1.append(TimeSignature("4/4"))
        # dotted eighth + sixteenth on the same beat: one dotted figure
        m1.append(Note("C4", quarterLength=0.75))
        m1.append(Note("D4", quarterLength=0.25))
        m1.append(Note("E4", quarterLength=1.0))
        m1.append(Note("F4", quarterLength=2.0))
        part.append(m1)
        m2 = Measure(number=2)
        m2.append(Note("G4", quarterLength=4.0))
        part.append(m2)
        measures = list(part.getElementsByClass(Measure))
        notes = [n for m in measures for n in m.notes]
        return {
            # keep the part referenced: music21 site context is weak
            "_part_keepalive": part,
            "notes": notes,
            "measures": measures,
            DATA_SOUNDING_MEASURES: [0, 1],
        }

    def test_rhythm_intensity_and_dotted(self):
        part_features = {}
        update_part_objects({}, self._part_data(), None, part_features)
        # RhythmInt = sum of durations / sounding beats = 8 / 8
        assert part_features["RhythmInt"] == 1.0
        # one dotted figure over 8 sounding beats
        assert part_features["DottedRhythm"] == 1 / 8
        assert part_features["DoubleDottedRhythm"] == 0.0

    def test_sounding_measures_matched_by_index(self):
        # only the first measure (index 0) sounding: 4 beats in denominator
        data = self._part_data()
        data[DATA_SOUNDING_MEASURES] = [0]
        part_features = {}
        update_part_objects({}, data, None, part_features)
        assert part_features["RhythmInt"] == 8 / 4
