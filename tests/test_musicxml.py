"""Unit tests for the score-preparation helpers of musif.musicxml.common:
melodic lines, the split of a staff shared by two players, and the
transposition to sounding pitch."""
from music21 import instrument
from music21.dynamics import Dynamic
from music21.expressions import TextExpression
from music21.interval import Interval
from music21.key import KeySignature
from music21.note import Note, Rest
from music21.stream import Measure, Part, Score, Voice

from musif.musicxml.common import (
    _get_intervals,
    get_notes_and_measures,
    split_layers,
    to_sounding_pitch,
)


def _measure(number, *pitches):
    """A 4/4 measure written in a single voice."""
    measure = Measure(number=number)
    for pitch in pitches:
        measure.append(Note(pitch, quarterLength=4 / len(pitches)))
    return measure


def _two_voice_measure(number, upper, lower):
    """A 4/4 measure written in two voices."""
    measure = Measure(number=number)
    for voice_id, pitches in (("1", upper), ("2", lower)):
        voice = Voice(id=voice_id)
        for pitch in pitches:
            voice.append(Note(pitch, quarterLength=4 / len(pitches)))
        measure.insert(0, voice)
    return measure


def _rest_measure(number):
    measure = Measure(number=number)
    measure.append(Rest(quarterLength=4))
    return measure


def _names(elements):
    return [element.nameWithOctave for element in elements if element.isNote]


def _lines(part):
    return [_names(line) for line in get_notes_and_measures(part)[-1]]


class TestMelodicLines:
    def _part(self):
        part = Part()
        part.append(_measure(1, "C5", "D5"))
        part.append(_two_voice_measure(2, ["E5", "F5"], ["C4", "C4"]))
        part.append(_measure(3, "G5", "A5"))
        part.append(_two_voice_measure(4, ["B5", "C6"], ["E4"]))
        return part

    def test_first_voice_continues_the_main_line(self):
        # measures in one voice and the first voice of measures in two are
        # the same line of music
        assert _lines(self._part())[0] == [
            "C5", "D5", "E5", "F5", "G5", "A5", "B5", "C6",
        ]

    def test_other_voices_start_anew_at_each_passage(self):
        # the second voice of m. 2 and that of m. 4 are separate lines:
        # nothing is measured between them over m. 3
        assert _lines(self._part())[1:] == [["C4", "C4"], ["E4"]]

    def test_no_interval_skips_a_two_voice_measure(self):
        # the lines used to follow music21's containers: the direct notes
        # joined D5 (m. 1) to G5 (m. 3), and D5-E5 and F5-G5 were lost
        part = self._part()
        lines = get_notes_and_measures(part)[-1]
        semitones = [
            interval.semitones
            for line in lines
            for interval in _get_intervals([e for e in line if e.isNote])
        ]
        assert semitones == [2, 2, 1, 2, 2, 2, 1, 0]

    def test_voice_spanning_consecutive_measures_is_one_passage(self):
        part = Part()
        part.append(_two_voice_measure(1, ["E5"], ["C4"]))
        part.append(_two_voice_measure(2, ["F5"], ["D4"]))
        assert _lines(part) == [["E5", "F5"], ["C4", "D4"]]

    def test_unwritten_measure_ends_the_main_line(self):
        # as in the second part of a split staff while the staff shows a
        # single line: the part is not written there, so no interval or
        # motion may run across the gap
        part = Part()
        part.insert(0, _measure(1, "C5", "D5"))
        part.insert(4, Measure(number=2))
        part.insert(8, _measure(3, "G5"))
        assert _lines(part) == [["C5", "D5"], ["G5"]]

    def test_rest_does_not_end_the_main_line(self):
        part = Part()
        part.append(_measure(1, "C5", "D5"))
        part.append(_rest_measure(2))
        part.append(_measure(3, "G5"))
        assert _lines(part) == [["C5", "D5", "G5"]]


def _horn_staff(two_instruments=False):
    """A horn staff shared by two players: two voices in mm. 1 and 4, a
    single line in m. 2, and a silent m. 3."""
    part = Part(id="P1")
    part.partName = "Corni in Re"
    part.insert(0, instrument.Horn())
    if two_instruments:
        # how music21 loads a horn that is not in F
        horn_in_d = instrument.Horn()
        horn_in_d.transposition = Interval("M2")
        part.insert(0, horn_in_d)
    first = _two_voice_measure(1, ["C5", "C5"], ["C4", "C4"])
    first.insert(0, TextExpression("a 2"))
    first.insert(0, TextExpression("Allegro"))
    first.insert(0, Dynamic("f"))
    first.insert(2, Dynamic("p"))
    second = _measure(2, "E5", "E5")
    second.insert(0, Dynamic("ff"))
    fourth = _two_voice_measure(4, ["G5"], ["E4"])
    fourth.insert(0, Dynamic("pp"))
    for measure in (first, second, _rest_measure(3), fourth):
        part.append(measure)
    score = Score()
    score.insert(0, part)
    return score


def _split(two_instruments=False):
    score = _horn_staff(two_instruments)
    split_layers(score, ["brass"])
    parts = list(score.parts)
    assert [p.partName for p in parts] == ["Corni in Re I", "Corni in Re II"]
    # keep the score referenced: music21 site context is weak
    return score, parts


def _dynamics(part):
    return [
        (measure.number, float(measure.elementOffset(mark)), mark.value)
        for measure in part.getElementsByClass(Measure)
        for mark in measure.getElementsByClass(Dynamic)
    ]


def _texts(part, number):
    measure = part.measure(number)
    return sorted(text.content for text in measure.getElementsByClass(TextExpression))


EXPECTED_DYNAMICS = [(1, 0.0, "f"), (1, 2.0, "p"), (2, 0.0, "ff"), (4, 0.0, "pp")]


class TestSplitLayers:
    def test_every_marking_of_a_measure_reaches_both_parts(self):
        # music21 holds any two Dynamics, and any two TextExpressions, to be
        # equal: only the first of each kind in a measure used to be copied,
        # which lost the "p" of m. 1 and the tempo word after "a 2"
        _score, parts = _split()
        for part in parts:
            assert _dynamics(part) == EXPECTED_DYNAMICS
            assert _texts(part, 1) == ["Allegro", "a 2"]

    def test_markings_stay_in_their_measure(self):
        # with two Instrument objects before the first measure, every
        # marking used to land one measure early and those of m. 1 were lost
        _score, parts = _split(two_instruments=True)
        for part in parts:
            assert _dynamics(part) == EXPECTED_DYNAMICS
            assert _texts(part, 1) == ["Allegro", "a 2"]

    def test_notes_are_not_duplicated(self):
        _score, (first, second) = _split()
        assert _names(first.recurse().notes) == ["C5", "C5", "E5", "E5", "G5"]
        assert _names(second.recurse().notes) == ["C4", "C4", "E4"]

    def test_staff_rest_is_a_rest_in_both_parts(self):
        # m. 3: the whole staff rests, so the second player rests too; m. 2:
        # the staff shows a single line, which goes to the first part only
        # and leaves the second part unwritten
        _score, (first, second) = _split()
        assert len(first.measure(3).getElementsByClass(Rest)) == 1
        assert len(second.measure(3).getElementsByClass(Rest)) == 1
        assert len(second.measure(2).notesAndRests) == 0

    def test_second_part_starts_anew_after_an_unwritten_measure(self):
        _score, (first, second) = _split()
        assert _lines(first) == [["C5", "C5", "E5", "E5", "G5"]]
        assert _lines(second) == [["C4", "C4"], ["E4"]]


class TestSplitCondition:
    def _staff(self, second_voice):
        part = Part(id="P1")
        part.partName = "Oboi"
        part.insert(0, instrument.Oboe())
        measure = Measure(number=1)
        upper = Voice(id="1")
        upper.append(Note("C5", quarterLength=4))
        lower = Voice(id="2")
        lower.append(second_voice)
        measure.insert(0, upper)
        measure.insert(0, lower)
        part.append(measure)
        part.append(_measure(2, "D5", "E5"))
        score = Score()
        score.insert(0, part)
        return score

    def test_stray_rest_in_a_second_voice_does_not_split_the_staff(self):
        # a leftover rest in voice 2 used to create a second part without a
        # single note (and, with it, undefined ratios against that part)
        score = self._staff(Rest(quarterLength=4))
        split_layers(score, ["wind"])
        assert [p.partName for p in score.parts] == ["Oboi"]
        assert _lines(score.parts[0]) == [["C5", "D5", "E5"]]

    def test_second_voice_with_notes_splits_the_staff(self):
        score = self._staff(Note("E4", quarterLength=4))
        split_layers(score, ["wind"])
        assert [p.partName for p in score.parts] == ["Oboi I", "Oboi II"]


def _musicxml_part(part_id, measures):
    """One <part>: a whole note C5 per measure; `measures` gives, for each
    measure, the (diatonic, chromatic) transposition it states, or None."""
    xml = f'<part id="{part_id}">'
    for number, transposition in enumerate(measures, 1):
        xml += f'<measure number="{number}"><attributes>'
        if number == 1:
            xml += (
                "<divisions>1</divisions><key><fifths>0</fifths></key>"
                "<time><beats>4</beats><beat-type>4</beat-type></time>"
                "<clef><sign>G</sign><line>2</line></clef>"
            )
        if transposition is not None:
            diatonic, chromatic = transposition
            xml += (
                f"<transpose><diatonic>{diatonic}</diatonic>"
                f"<chromatic>{chromatic}</chromatic></transpose>"
            )
        xml += (
            "</attributes><note><pitch><step>C</step><octave>5</octave></pitch>"
            "<duration>4</duration><type>whole</type></note></measure>"
        )
    return xml + "</part>"


def _musicxml_score(tmp_path, horn_measures):
    """A horn part stating the given transpositions and a violin part."""
    path = tmp_path / "score.xml"
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<score-partwise version="3.1"><part-list>'
        '<score-part id="P1"><part-name>Corni</part-name>'
        '<score-instrument id="P1-I1"><instrument-name>Horn</instrument-name>'
        "<instrument-sound>brass.french-horn</instrument-sound>"
        "</score-instrument></score-part>"
        '<score-part id="P2"><part-name>Violino</part-name>'
        '<score-instrument id="P2-I1"><instrument-name>Violin</instrument-name>'
        "<instrument-sound>strings.violin</instrument-sound>"
        "</score-instrument></score-part></part-list>"
        + _musicxml_part("P1", horn_measures)
        + _musicxml_part("P2", [None] * len(horn_measures))
        + "</score-partwise>"
    )
    return path


class TestSoundingPitchFromTheFile:
    def _sounding(self, tmp_path, horn_measures):
        from music21 import converter

        path = _musicxml_score(tmp_path, horn_measures)
        score = converter.parse(str(path))
        to_sounding_pitch(score, str(path))
        horn, violin = score.parts
        return _names(horn.recurse().notes), _names(violin.recurse().notes)

    def test_each_transposition_applies_from_its_measure(self, tmp_path):
        # in D (a tone up), then in F (a fifth down), then at pitch again
        horn, violin = self._sounding(tmp_path, [(1, 2), (-4, -7), (0, 0)])
        assert horn == ["D5", "F4", "C5"]
        assert violin == ["C5", "C5", "C5"]

    def test_measures_before_the_first_transposition_are_untouched(self, tmp_path):
        # music21 gives a horn the default transposition of a horn in F and
        # used to apply it to the opening measures, where the file states
        # nothing at all
        horn, _ = self._sounding(tmp_path, [None, None, (1, 2)])
        assert horn == ["C5", "C5", "D5"]

    def test_transposition_equal_to_the_default_is_still_dated(self, tmp_path):
        # stated in the third measure only, and equal to music21's default
        # for the horn: music21 creates no new instrument there, so its own
        # conversion cannot know where the transposition begins
        horn, _ = self._sounding(tmp_path, [None, None, (-4, -7)])
        assert horn == ["C5", "C5", "F4"]

    def test_part_without_transposition_is_untouched(self, tmp_path):
        horn, _ = self._sounding(tmp_path, [None, None, None])
        assert horn == ["C5", "C5", "C5"]


class TestSoundingPitch:
    """Without the file, music21's reading of the instruments is used."""

    def _part(self, name, part_instruments, key_sharps, pitch):
        part = Part()
        part.partName = name
        for part_instrument in part_instruments:
            part.insert(0, part_instrument)
        measure = Measure(number=1)
        measure.insert(0, KeySignature(key_sharps))
        measure.append(Note(pitch, quarterLength=4))
        part.append(measure)
        return part

    def _score(self):
        # a horn in E flat as music21 loads it: the default horn (in F)
        # followed by the one carrying the transposition found in the file
        horn_in_e_flat = instrument.Horn()
        horn_in_e_flat.transposition = Interval("M-6")
        transposing = self._part(
            "Corni in Mib", [instrument.Horn(), horn_in_e_flat], 0, "C5"
        )
        transposing.atSoundingPitch = False
        # a horn in C: the file states no transposition
        at_pitch = self._part("Corni in Do", [instrument.Horn()], -3, "E-4")
        at_pitch.atSoundingPitch = True
        violin = self._part("Violino I", [instrument.Violin()], -3, "E-5")
        score = Score()
        for part in (transposing, at_pitch, violin):
            score.insert(0, part)
        return score

    def _first_note(self, part):
        return part.recurse().notes.first().nameWithOctave

    def _key(self, part):
        return part.recurse().getElementsByClass(KeySignature).first().sharps

    def test_transposing_part_is_read_as_it_sounds(self):
        score = self._score()
        to_sounding_pitch(score)
        horns = score.parts[0]
        # written C5 sounds a major sixth lower
        assert self._first_note(horns) == "E-4"

    def test_key_signature_is_transposed_once(self):
        # with the default instrument left in place, the opening key
        # signature was transposed by both: C major came out as A flat major
        score = self._score()
        to_sounding_pitch(score)
        horns = score.parts[0]
        assert self._key(horns) == -3
        assert len(horns.getElementsByClass(instrument.Instrument)) == 1

    def test_parts_without_transposition_are_untouched(self):
        score = self._score()
        to_sounding_pitch(score)
        _horns, at_pitch, violin = score.parts
        assert self._first_note(at_pitch) == "E-4"
        assert self._key(at_pitch) == -3
        assert self._first_note(violin) == "E-5"
