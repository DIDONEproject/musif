from copy import deepcopy
from typing import List, Tuple
from xml.etree import ElementTree
import itertools

from music21.chord import Chord
from music21.instrument import Instrument
from music21.interval import Interval
from music21.key import KeySignature
from music21.musicxml.xmlToM21 import MeasureParser
from music21.note import GeneralNote, Note, Rest
from music21.bar import Repeat
from music21.repeat import RepeatMark
from music21.scale import MajorScale, MinorScale
from music21.stream.base import Measure, Part, Score, Voice
from music21.text import assembleLyrics
from roman import toRoman

from musif.cache import isinstance
from musif.logs import pwarn


def is_voice(part: Part) -> bool:
    """
    Returns True if the part is a singer part, otherwise returns False

    Parameters
    ----------
    part : Part
      Music21 part to check if it's a singer part
    """

    instrument = part.getInstrument(returnDefault=False)
    if instrument is None or instrument.instrumentSound is None:
        return False
    return "voice" in instrument.instrumentSound


def name_parts(score: Score):
    """
    This function assign a name to each part in the score. If a name is already present,
    we keep it there, otherwise, we create a name of type `missingName#` where # is an
    incremental number,
    """
    i = 0
    for part in score.parts:
        increment = False
        if part.partName is None:
            part.partName = f"NoName{i}"
            increment = True
        if part.partAbbreviation is None:
            part.partAbbreviation = f"NoName{i}"
            increment = True
        if increment:
            i += 1


def _stated_transpositions(file_path):
    """
    The transpositions a MusicXML file states: for each part, in order, the
    number of its measures and a list of (index of the measure, interval),
    one entry per measure that carries a `<transpose>`.

    Returns None when the file cannot be read this way: it is not plain
    part-wise MusicXML (a compressed file, another format), or it states a
    transposition for one staff of a part only.
    """
    try:
        root = ElementTree.parse(file_path).getroot()
    except Exception:
        return None
    parts = root.findall("part")
    if len(parts) == 0:
        return None
    # music21's own reading of a <transpose> element, so that the intervals
    # are the ones music21 would have attached to the instruments
    reader = MeasureParser()
    stated = []
    for part in parts:
        measures = part.findall("measure")
        transpositions = {}
        for index, measure in enumerate(measures):
            for mx_transpose in measure.findall("attributes/transpose"):
                if mx_transpose.get("number") is not None:
                    return None
                transpositions[index] = reader.xmlTransposeToInterval(mx_transpose)
        stated.append((len(measures), sorted(transpositions.items())))
    return stated


def to_sounding_pitch(score: Score, file_path=None) -> None:
    """
    Transposes the score, in place, to sounding pitch: afterwards the notes,
    chords and key signatures of every transposing instrument (horns,
    trumpets, clarinets...) are the ones that sound. Only the transpositions
    the file states are applied, each from the measure that states it: a part
    that states none is left as it is, and so are the measures before the
    first one a part states.

    Parameters
    ----------
    score : Score
        Music21 score to transpose
    file_path : str, optional
        The MusicXML file the score was read from. The transpositions are
        taken from it, measure by measure. music21 alone cannot give them: it
        attaches to every instrument a default transposition (a horn is in F
        unless told otherwise) that cannot be told from one the file states,
        and would apply it to the measures in which the file states nothing.
        Without the file, or when it cannot be matched to the score part by
        part, music21's reading of the instruments is used.
    """
    parts = list(score.parts)
    stated = _stated_transpositions(file_path) if file_path else None
    if stated is not None and (
        len(stated) != len(parts)
        or any(
            len(part.getElementsByClass(Measure)) != number_of_measures
            for part, (number_of_measures, _) in zip(parts, stated)
        )
    ):
        stated = None

    if stated is None:
        for part in parts:
            # A part whose transposition differs from the default of its
            # instrument is loaded with two Instrument objects at the same
            # place: the default one, and next to it the one carrying the
            # transposition written in the file. Only the latter is in
            # force; left in place, the former would transpose the opening
            # key signature a second time.
            instruments = list(part.getElementsByClass(Instrument))
            for earlier, later in zip(instruments, instruments[1:]):
                if part.elementOffset(earlier) == part.elementOffset(later):
                    part.remove(earlier)
        score.toSoundingPitch(inPlace=True)
        return

    for part, (_, transpositions) in zip(parts, stated):
        measures = list(part.getElementsByClass(Measure))
        for position, (first, interval) in enumerate(transpositions):
            if position + 1 < len(transpositions):
                last = transpositions[position + 1][0]
            else:
                last = len(measures)
            if interval is None or interval.name == "P1":
                continue
            for measure in measures[first:last]:
                measure.transpose(
                    interval, inPlace=True, classFilterList=(Note, Chord, KeySignature)
                )
        # nothing is left to transpose, whatever the instruments say
        for stream in part.recurse(streamsOnly=True, includeSelf=True):
            stream.atSoundingPitch = True
    score.atSoundingPitch = True


def split_layers(score: Score, split_keywords: List[str]):
    """
    Function used to split possible layers. Those instruments that include to parts in the same staff
    will be separated in two diferent parts so they can be treated separately.

    Parameters
    ----------
    score : Score
        Music21 score to scan and separate parts in it according to split_keywords list

    split_keywords: List[str]
        List containing key words of instruments susceptible to be splitted. i.e. [oboe, viola]

    """

    final_parts = []
    for part_index, part in enumerate(score.parts):
        instrument = part.getInstrument(returnDefault=False)

        possible_layers = False
        if instrument is not None and instrument.instrumentSound is not None:
            for keyword in split_keywords:
                if keyword in instrument.instrumentSound:
                    possible_layers = True
                    break

        if possible_layers:
            # The staff is split only if a second player really has something
            # to play: a measure written in several voices in which a voice
            # other than the first carries notes. A stray rest in a second
            # voice (a leftover of the engraving, often invisible) used to
            # split the staff and leave a second part without a single note.
            has_second_voice = any(
                len(voice.notes) > 0
                for measure in part.getElementsByClass(Measure)
                for voice in list(measure.voices)[1:]
            )

            if has_second_voice:
                _separate_info_in_two_parts(score, final_parts, part)
            else:
                final_parts.append(part)  # without any change
                score.remove(part)
        else:
            final_parts.append(part)  # without any change
            score.remove(part)

    for idx, part in enumerate(final_parts):
        try:
            score.insert(0, part)
        except Exception:
            pass


def get_notes_and_measures(
    part: Part,
) -> Tuple[List[Note], List[Note], List[Measure], List[Measure]]:
    """
    Obtains lists of notes, tied notes, measures, measures that containg notes, and notes and rests.
    Information that is useful in the subsequent process of extraction.

    Parameters
    ----------
    part : Part
      Music21 part to extract the info from.

    """

    measures = list(part.getElementsByClass(Measure))
    # collect notes from the measure itself AND from its Voice sub-streams:
    # Measure.notes is non-recursive, and whole parts written in voices used
    # to be reported as silent. Chords are excluded from the note lists (but
    # their measures still count as sounding) - see Feature_definition.md.
    #
    # Elements are also grouped into MELODIC LINES: intervals and motion must
    # never be computed across simultaneous lines, or leaps are fabricated at
    # every voice boundary.
    #
    # - The MAIN line runs through the whole part: the direct elements of the
    #   measures written in one voice, continued by the FIRST voice of the
    #   measures written in several. music21 stores the two kinds of measure
    #   differently, but they are the same line of music; keeping them apart
    #   joined the measure before a two-voice passage to the measure after it.
    # - Every OTHER voice is a line of its own that starts anew at each
    #   passage (a run of consecutive measures where that voice is written),
    #   so nothing is measured from one passage to the next over the measures
    #   in between.
    # - A measure where nothing at all is written for the part (as in the
    #   second part of a split staff while the staff shows a single line)
    #   ends the main line in the same way; it starts anew afterwards.
    notes_per_measure = []
    notes_and_rests = []
    main_line = []
    lines = [main_line]
    passages = {}
    for measure in measures:
        measure_notes = list(measure.notes)
        direct_elements = list(measure.notesAndRests)
        notes_and_rests.extend(direct_elements)
        main_line.extend(direct_elements)
        written = len(direct_elements) > 0
        voices_here = set()
        for position, voice in enumerate(measure.voices):
            voice_elements = list(voice.notesAndRests)
            measure_notes.extend(voice.notes)
            notes_and_rests.extend(voice_elements)
            written = written or len(voice_elements) > 0
            if position == 0:
                main_line.extend(voice_elements)
                continue
            voice_id = str(voice.id)
            voices_here.add(voice_id)
            if voice_id not in passages:
                passages[voice_id] = []
                lines.append(passages[voice_id])
            passages[voice_id].extend(voice_elements)
        for voice_id in [v for v in passages if v not in voices_here]:
            del passages[voice_id]
        if not written and len(main_line) > 0:
            main_line = []
            lines.append(main_line)
        notes_per_measure.append(measure_notes)

    melodic_lines = [
        line
        for line in lines
        if any(isinstance(element, Note) for element in line)
    ]

    sounding_measures = [
        idx for idx, measure_notes in enumerate(notes_per_measure)
        if len(measure_notes) > 0
    ]
    original_notes = [
        note
        for measure_notes in notes_per_measure
        for note in measure_notes
        if isinstance(note, Note)
    ]
    if len(original_notes) == 0 and len(measures) > 0:
        pwarn(
            f"Part '{part.partName}' yielded no notes; its note-based features "
            "will be empty"
        )

    return original_notes, measures, sounding_measures, notes_and_rests, melodic_lines


def _already_in(target: Measure, element, offset) -> bool:
    """
    Whether `target` already holds `element`, or a twin of it, at `offset`
    (None for an element stored at the end of its measure, such as the right
    barline).

    music21's equality is too coarse to decide this alone: any two Dynamics,
    and any two TextExpressions, compare equal whatever their value or
    content. A plain ``element in target.elements`` test therefore dropped
    every marking after the first of its kind in the measure.
    """
    for other in target.elements:
        if other is element:
            return True
        if type(other) is not type(element) or other != element:
            continue
        if any(
            getattr(other, attribute, None) != getattr(element, attribute, None)
            for attribute in ("value", "content")
        ):
            continue
        other_offset = target.elementOffset(other, returnSpecial=True)
        other_at_end = isinstance(other_offset, str)
        if offset is None:
            if other_at_end:
                return True
        elif not other_at_end and abs(float(other_offset) - float(offset)) < 1e-6:
            return True
    return False


def _separate_info_in_two_parts(score, final_parts, part):
    parts_splitted = part.voicesToParts().elements
    source_measures = [m for m in part.elements if isinstance(m, Measure)]
    for p in parts_splitted:
        # Pair every measure with its twin by position in time. Counting the
        # elements of the split part instead put the markings one measure
        # early whenever more than one element preceded its first measure
        # (transposing instruments carry two Instrument objects).
        targets = {
            float(p.elementOffset(m)): m for m in p.getElementsByClass(Measure)
        }
        for measure in source_measures:
            target = targets.get(float(part.elementOffset(measure)))
            if target is None:
                continue
            # add the information music21 leaves out of the split parts:
            # clefs, dynamics, text annotations... Notes are never copied
            # (that used to duplicate the measure's direct notes in every
            # part), and rests only when the whole staff rests, so that the
            # measure is a silence in every split part and not a gap.
            staff_rests = len(measure.notes) == 0 and not any(
                isinstance(e, Voice) for e in measure.elements
            )
            for e in measure.elements:
                if isinstance(e, Voice):
                    continue
                if isinstance(e, GeneralNote) and not (
                    staff_rests and isinstance(e, Rest)
                ):
                    continue
                offset = measure.elementOffset(e, returnSpecial=True)
                if isinstance(offset, str):
                    # stored at the end of the measure (right barline)
                    if not _already_in(target, e, None):
                        target.storeAtEnd(deepcopy(e))
                elif not _already_in(target, e, offset):
                    # insert at the element's real offset: rebuilding
                    # .elements dropped every offset to 0 (dynamics and
                    # tempo marks all landed on the downbeat) and
                    # cleared the measure's end elements (barlines)
                    target.insert(offset, deepcopy(e))
    for num, p in enumerate(parts_splitted, 1):
        p.id = part.id + " " + toRoman(num)  # only I or II
        p.partName = part.partName + " " + toRoman(num)  # only I or II
        # p.elements = p.elements
        final_parts.append(p)

    score.remove(part)


def _get_part_clef(part):
    """
    Extracts the clef in the score by checking the first measure of the part

    Parameters
    ----------
        part : Part
      Music21 part to extract the info from

    """
    for elem in part.elements:
        if isinstance(elem, Measure):
            if hasattr(elem, "clef"):
                return elem.clef.sign + "-" + str(elem.clef.line)
    return ""


def _get_degrees_and_accidentals(key: str, notes: List[Note]) -> List[Tuple[str, str]]:
    if "major" in key.split():
        scl = MajorScale(key.split(" ")[0])
    else:
        scl = MinorScale(key.split(" ")[0])

    degrees = [
        scl.getScaleDegreeAndAccidentalFromPitch(note.pitches[0]) for note in notes
    ]

    return [(degree[0], degree[1].fullName if degree[1] else "") for degree in degrees]


def _get_intervals(notes: List[Note]) -> List[Interval]:
    return [
        Interval(notes[i].pitches[0], notes[i + 1].pitches[0])
        for i in range(len(notes) - 1)
    ]


def _contains_text(part: Part) -> bool:
    return assembleLyrics(part)


def _get_lyrics_in_notes(notes: List[Note]) -> List[str]:
    lyrics = []
    for note in notes:
        if note.lyrics is None or len(note.lyrics) == 0:
            continue
        note_lyrics = [
            syllable.text for syllable in note.lyrics if syllable.text is not None
        ]
        lyrics.extend(note_lyrics)
    return lyrics


def fix_repeats(score: Score):
    """Fix the repeat sign in the score by ensuring that all the parts have
    the same signs"""
    signs = score.recurse().getElementsByClass("RepeatMark")
    # measure_parts is an iterator, but successive loops won't restart from index
    # 0 but from where the previous one was left
    # for this, we use itertools.chain to force the creation of a proper
    # iterator
    measure_parts = [
        itertools.chain(p.getElementsByClass("Measure")) for p in score.parts
    ]
    for sign in signs:
        measure_sign = sign.activeSite
        measure_sign_offset = measure_sign.offset
        offset_sign = sign.offset
        for measures in measure_parts:
            for m in measures:
                if m.offset == measure_sign_offset:
                    marks = m.getElementsByClass("RepeatMark")
                    if sign.__class__ not in [mark.__class__ for mark in marks]:
                        if isinstance(sign, Repeat):
                            # repeat barlines only take effect as the measure's
                            # left/right barline: inserted mid-stream they are
                            # invisible to expandRepeats, and sharing one
                            # object across parts corrupts its sites
                            if sign.direction == "start":
                                m.leftBarline = deepcopy(sign)
                            else:
                                m.rightBarline = deepcopy(sign)
                        else:
                            m.insert(offset_sign, deepcopy(sign))
                    break
