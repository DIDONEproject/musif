import copy
from typing import List, Tuple, Union

from music21 import *
from music21.note import Note
from music21.stream import Part, Score
from roman import toRoman

from musif.common import group

MUSICXML_FILE_EXTENSION = "xml"


def is_voice(part: Part) -> bool:
    instrument = part.getInstrument(returnDefault=False)
    if instrument is None or instrument.instrumentSound is None:
        return False
    return "voice" in instrument.instrumentSound


def split_wind_layers(score: Score, split_keywords: List[str]):
    """
    Function used to split the possible layers present on wind instruments

    """
    final_parts = []
    for part_index, part in enumerate(score.parts):
        instrument = part.getInstrument(returnDefault=False)

        possible_layers = False
        for keyword in split_keywords:
            if keyword in instrument.instrumentSound:
                possible_layers = True
                break

        if possible_layers:  # ONLY WIND INSTRUMENTS
            has_voices = False
            for measure in part.elements:
                if isinstance(measure, stream.Measure) and any(isinstance(e, stream.Voice) for e in measure.elements):
                    has_voices = True
                    break

            if has_voices:  # recorrer los compases buscando las voices y separamos en dos parts
                parts_splitted = part.voicesToParts().elements
                num_measure = 0
                for measure in part.elements:
                    # add missing information to both parts (dynamics, text annotations, etc are missing)
                    if isinstance(measure, stream.Measure) and any(
                        not isinstance(e, stream.Voice) for e in measure.elements
                    ):
                        not_voices_elements = [
                            e for e in measure.elements if not isinstance(e, stream.Voice)
                        ]  # elements such as clefs, dynamics, text annotations...
                        # introducimos esta información en cada voz:
                        for p in parts_splitted:
                            p.elements[num_measure].elements += tuple(
                                e for e in not_voices_elements if e not in p.elements[num_measure].elements
                            )
                        num_measure += 1
                for num, p in enumerate(parts_splitted, 1):
                    p_copy = copy.deepcopy(part)
                    p_copy.id = p_copy.id + " " + toRoman(num)  # only I or II
                    p_copy.partName = p_copy.partName + " " + toRoman(num)  # only I or II
                    p_copy.elements = p.elements
                    final_parts.append(p_copy)
                score.remove(part)
            else:
                final_parts.append(part)  # without any change
                score.remove(part)
        else:
            final_parts.append(part)  # without any change
            score.remove(part)

    for part in final_parts:
        try:
            score.insert(0, part)
        except:
            pass  # already inserted


def get_part_clef(part):
    # the clef is in measure 1
    for elem in part.elements:
        if isinstance(elem, stream.Measure):
            if hasattr(elem, "clef"):
                return elem.clef.sign + "-" + str(elem.clef.line)
    return ""


def get_xml_scoring_variables(score):
    #################################################################################
    # Function to get the aria's scoring information
    #################################################################################
    # PRUEBAS CON SORTINGGROUPINGS
    return group.get_scoring(score)


def get_key(score: Score) -> str:
    return str(score.analyze("key"))


def get_degrees_and_accidentals(key: str, notes: List[Note]) -> List[Tuple[str, str]]:
    if "major" in key:
        scl = scale.MajorScale(key.split(" ")[0])
    else:
        scl = scale.MinorScale(key.split(" ")[0])

    degrees = [scl.getScaleDegreeAndAccidentalFromPitch(note.pitches[0]) for note in notes]

    return [(degree[0], degree[1].fullName if degree[1] else "") for degree in degrees]


def get_intervals(notes: List[Note]) -> Tuple[List[Union[int, float]], List[str]]:
    """
    my_interval_list is a list of tuples where we insert intervals in both variables types: numeric (in semitones) and nominal (name)
    """
    numeric_intervals = []
    text_intervals = []
    for i in range(len(notes) - 1):
        note = notes[i]
        next_note = notes[i + 1]
        i = interval.Interval(note.pitches[0], next_note.pitches[0])
        numeric_intervals.append(i.semitones)
        text_intervals.append(i.directedName)
    return numeric_intervals, text_intervals


def contains_text(part: Part) -> bool:
    return text.assembleLyrics(part)


def get_notes_lyrics(notes: List[Note]) -> List[str]:
    return [note.lyric for note in notes if note.lyrics and note.lyrics[0].text is not None]


