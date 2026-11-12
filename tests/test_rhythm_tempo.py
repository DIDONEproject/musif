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

    def _one_beat_measures(self, first, second):
        """Two 3/8 measures (one beat each) holding the given durations."""
        part = Part()
        for number, durations in ((1, first), (2, second)):
            measure = Measure(number=number)
            if number == 1:
                measure.append(TimeSignature("3/8"))
            for duration in durations:
                measure.append(Note("C4", quarterLength=duration))
            part.append(measure)
        measures = list(part.getElementsByClass(Measure))
        return {
            "_part_keepalive": part,
            "notes": [n for m in measures for n in m.notes],
            "measures": measures,
            DATA_SOUNDING_MEASURES: [0, 1],
        }

    def test_dotted_figure_does_not_cross_the_barline(self):
        # every note of a 3/8 measure is on beat 1, so the dotted eighth that
        # ends the first measure used to be paired with the sixteenth on the
        # next downbeat
        data = self._one_beat_measures([0.75, 0.75], [0.25, 0.25, 1.0])
        part_features = {}
        update_part_objects({}, data, None, part_features)
        assert part_features["DottedRhythm"] == 0

    def test_dotted_figure_within_a_one_beat_measure(self):
        # dotted eighth + sixteenth inside each measure: two figures over
        # two sounding beats
        data = self._one_beat_measures([0.75, 0.25, 0.5], [0.5, 0.75, 0.25])
        part_features = {}
        update_part_objects({}, data, None, part_features)
        assert part_features["DottedRhythm"] == 2 / 2


class TestWindowMetre:
    def test_window_slice_reads_prevailing_metre_from_context(self):
        # a window sliced with .measures(...) carries the prevailing time
        # signature at Part level, not inside its first measure; both TS
        # readers must resolve it from context instead of falling back to
        # the score's opening metre (round-2 R2-1)
        from music21.meter import TimeSignature
        from music21.note import Note
        from music21.stream import Measure, Part

        from musif.extract.constants import (
            DATA_FILTERED_PARTS,
            GLOBAL_TIME_SIGNATURE,
        )
        from musif.extract.features.core.handler import _get_time_signature
        from musif.extract.features.tempo.handler import extract_time_signatures

        part = Part()
        for index in range(10):
            measure = Measure(number=index + 1)
            if index == 0:
                measure.append(TimeSignature("3/4"))
            if index == 4:
                measure.append(TimeSignature("2/2"))
            for _ in range(3):
                measure.append(Note("C4", quarterLength=1.0))
            part.append(measure)
        window = part.measures(5, 9, indicesNotNumbers=True)  # all in 2/2
        score_data = {
            DATA_FILTERED_PARTS: [window],
            GLOBAL_TIME_SIGNATURE: TimeSignature("3/4"),
        }
        assert _get_time_signature(score_data) == "2/2"
        time_signature, _, per_measure, grouped, beats = extract_time_signatures(
            list(window.getElementsByClass(Measure)), score_data
        )
        assert time_signature == "2/2"
        assert set(per_measure) == {"2/2"}
        assert beats == 2
        assert grouped == "simple duple"


class TestRatesPerQuarterNote:
    def test_rhythm(self):
        helper = TestRhythmFormulas()
        data = helper._one_beat_measures([0.75, 0.25, 0.5], [0.5, 0.75, 0.25])
        features = {}
        update_part_objects({}, data, None, features)
        # two measures of 3/8: two beats, but three quarter notes
        assert features["RhythmInt"] == 3.0 / 2
        assert features["RhythmIntQuarters"] == 3.0 / 3
        assert features["DottedRhythm"] == 2 / 2
        assert features["DottedRhythmQuarters"] == 2 / 3

    def test_quarter_length_of_a_measure(self):
        from musif.musicxml.tempo import get_quarter_length

        assert get_quarter_length("4/4") == 4
        assert get_quarter_length("2/2") == 4
        assert get_quarter_length("3/8") == 1.5
        assert get_quarter_length("6/8") == 3
        assert get_quarter_length("C") == 4


class TestTempoWords:
    def test_tempo_giusto_and_comodo(self):
        # "tempo" used to win over the word that says which tempo
        assert get_tempo_grouped_1("Tempo giusto") == "Giusto"
        assert get_tempo_grouped_2("Giusto") == "Moderate"
        assert get_tempo_grouped_1("Tempo comodo") == "Comodo"
        assert get_tempo_grouped_1("A tempo") == "A tempo"
        assert get_tempo_grouped_2("A tempo") == "NA"

    def test_spellings(self):
        assert get_tempo_grouped_1("Tempo di Menuet") == "Minuetto"
        assert get_tempo_grouped_2(get_tempo_grouped_1("Adaggissimo")) == "Slow"
        assert get_tempo_grouped_2(get_tempo_grouped_1("Furioso")) == "Fast"

    def _part(self, *measures):
        from music21.expressions import TextExpression

        part = Part()
        for number, texts in measures:
            measure = Measure(number=number)
            for text in texts:
                measure.insert(0, TextExpression(text))
            measure.append(Note("C4", quarterLength=4))
            part.append(measure)
        return part

    def _tempo(self, part):
        from musif.extract.constants import DATA_NUMERIC_TEMPO
        from musif.extract.features.tempo.handler import extract_tempo

        return extract_tempo({DATA_NUMERIC_TEMPO: "NA"}, part)[1]

    def test_heading_is_the_first_tempo_word_of_the_measure(self):
        # an expression mark later in the measure used to replace it
        part = self._part((1, ["Allegro moderato", "sostenuto"]))
        assert self._tempo(part) == "Allegro moderato"

    def test_heading_over_the_first_full_measure_after_a_pickup(self):
        part = self._part((0, []), (1, ["Andante"]))
        assert self._tempo(part) == "Andante"

    def test_only_the_opening_counts(self):
        part = self._part((1, []), (2, ["Presto"]))
        assert self._tempo(part) == "NA"


class TestRepriseInstruction:
    def _file(self, tmp_path, direction):
        path = tmp_path / "score.xml"
        path.write_text(
            '<score-partwise><part id="P1"><measure number="1">'
            + direction
            + "</measure></part></score-partwise>"
        )
        return str(path)

    def _value(self, tmp_path, direction):
        from musif.musicxml.tempo import extract_reprise_instruction

        return extract_reprise_instruction(self._file(tmp_path, direction))

    def test_da_capo_as_playback_instruction(self, tmp_path):
        assert self._value(tmp_path, '<direction><sound dacapo="yes"/></direction>') == 1

    def test_dal_segno_as_words(self, tmp_path):
        direction = "<direction><direction-type><words>D.S. al Fine</words></direction-type></direction>"
        assert self._value(tmp_path, direction) == 1

    def test_other_words_are_not_an_instruction(self, tmp_path):
        direction = "<direction><direction-type><words>dolce</words></direction-type></direction>"
        assert self._value(tmp_path, direction) == 0

    def test_unreadable_file(self, tmp_path):
        from musif.musicxml.tempo import extract_reprise_instruction

        assert extract_reprise_instruction(str(tmp_path / "missing.xml")) == "NA"
