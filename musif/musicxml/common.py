import copy
from typing import Dict, List, Tuple, Union

from music21 import *
from music21.note import Note
from music21.stream import Measure, Part, Score
from music21.converter import parse
from pandas import DataFrame

from musif.config import sound_to_family
from musif.common import group

MUSICXML_FILE_EXTENSION = "xml"


def is_voice(part: Part) -> bool:
    instrument = part.getInstrument(returnDefault=False)
    if instrument is None or instrument.instrumentSound is None:
        return False
    return "voice" in instrument.instrumentSound



def flat_layers(score):
    """
    Function used to split the possible layers present on wind instruments

    """
    final_parts = []
    for part_index, part in enumerate(score.parts):
        possible_layers = False
        # GET ONLY WOODWIND OR BRASS INSTRUMENTS
        i = part.getInstrument(returnDefault=False)
        if hasattr(i, "instrumentSound") and i.instrumentSound is not None:  # FINALE
            if "woodwind" in i.instrumentSound or "brass" in i.instrumentSound or "wind" in i.instrumentSound:
                possible_layers = True
        elif hasattr(i, "instrumentName"):  # MUSESCORE
            name, family = group.get_musescoreInstrument_nameAndFamily(i, sound_to_family, part)
            if family in ["woodwind", "brass"]:
                possible_layers = True

        if possible_layers:  # ONLY WIND INSTRUMENTS
            has_voices = False
            for measure in part.elements:
                if isinstance(measure, stream.Measure) and any(isinstance(e, stream.Voice) for e in measure.elements):
                    has_voices = True
                    break

            if has_voices:  # recorrer los compases buscando las voices y separamos en dos parts
                parts_splited = part.voicesToParts().elements
                num_measure = 0
                for (
                    measure
                ) in (
                    part.elements
                ):  # add missing information to both parts (dynamics, text annotations, etc are missing)
                    if isinstance(measure, stream.Measure) and any(
                        not isinstance(e, stream.Voice) for e in measure.elements
                    ):
                        not_voices_elements = [
                            e for e in measure.elements if not isinstance(e, stream.Voice)
                        ]  # elements such as clefs, dynamics, text annotations...
                        # introducimos esta información en cada voz:
                        for p in parts_splited:
                            p.elements[num_measure].elements += tuple(
                                e for e in not_voices_elements if e not in p.elements[num_measure].elements
                            )
                        num_measure += 1
                for num, p in enumerate(parts_splited):
                    p_copy = copy.deepcopy(part)
                    p_copy.id = p_copy.id + " " + "I" * (num + 1)  # only I or II
                    p_copy.partName = p_copy.partName + " " + "I" * (num + 1)  # only I or II
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


def split_wind_layers(score: Score):
    """
    Function used to split the possible layers present on wind instruments

    """
    final_parts = []
    for part_index, part in enumerate(score.parts):
        possible_layers = False
        # GET ONLY WOODWIND OR BRASS INSTRUMENTS
        i = part.getInstrument(returnDefault=False)
        if hasattr(i, "instrumentSound") and i.instrumentSound is not None:  # FINALE
            if "woodwind" in i.instrumentSound or "brass" in i.instrumentSound or "wind" in i.instrumentSound:
                possible_layers = True

        if possible_layers:  # ONLY WIND INSTRUMENTS
            has_voices = False
            for measure in part.elements:
                if isinstance(measure, stream.Measure) and any(isinstance(e, stream.Voice) for e in measure.elements):
                    has_voices = True
                    break

            if has_voices:  # recorrer los compases buscando las voices y separamos en dos parts
                parts_splited = part.voicesToParts().elements
                num_measure = 0
                for (
                    measure
                ) in (
                    part.elements
                ):  # add missing information to both parts (dynamics, text annotations, etc are missing)
                    if isinstance(measure, stream.Measure) and any(
                        not isinstance(e, stream.Voice) for e in measure.elements
                    ):
                        not_voices_elements = [
                            e for e in measure.elements if not isinstance(e, stream.Voice)
                        ]  # elements such as clefs, dynamics, text annotations...
                        # introducimos esta información en cada voz:
                        for p in parts_splited:
                            p.elements[num_measure].elements += tuple(
                                e for e in not_voices_elements if e not in p.elements[num_measure].elements
                            )
                        num_measure += 1
                for num, p in enumerate(parts_splited):
                    p_copy = copy.deepcopy(part)
                    p_copy.id = p_copy.id + " " + "I" * (num + 1)  # only I or II
                    p_copy.partName = p_copy.partName + " " + "I" * (num + 1)  # only I or II
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


def set_ties(subject, my_notes_list):
    """
    This function converts tied notes into a unique note
    """
    if not isinstance(subject, note.Note):
        return
    if subject.tie is None:
        my_notes_list.append(subject)
        return
    if subject.tie.type != "stop" and subject.tie.type != "continue":
        my_notes_list.append(subject)
        return
    if isinstance(my_notes_list[-1], note.Note):
        my_notes_list[-1].duration.quarterLength += subject.duration.quarterLength  # sum tied notes' length
        return
    back_counter = -1
    while isinstance(my_notes_list[back_counter], tuple):
        back_counter -= -1
    else:
        my_notes_list[
            back_counter
        ].duration.quarterLength += subject.duration.quarterLength  # sum tied notes' length across measures


def get_measures(part: Part) -> List[Measure]:
    return [element for element in part.elements if isinstance(element, Measure)]


def get_notes(part: Part) -> List[Note]:
    my_notes_list = []
    for measure in get_measures(part):
        for note in measure.notes:
            set_ties(note, my_notes_list)
    return my_notes_list


def get_key(score: Score) -> str:
    return str(score.analyze("key"))


def get_degrees_and_accidentals(key: str, notes: List[Note]) -> List[Tuple[str, str]]:
    if "major" in key:
        scl = scale.MajorScale(key.split(" ")[0])
    else:
        scl = scale.MinorScale(key.split(" ")[0])

    degrees = [scl.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch(note.name)) for note in notes]

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
        i = interval.Interval(noteStart=note, noteEnd=next_note)
        numeric_intervals.append(i.semitones)
        text_intervals.append(i.directedName)
    return numeric_intervals, text_intervals


def contains_text(part: Part) -> bool:
    return text.assembleLyrics(part)


def get_notes_lyrics(notes: List[Note]) -> List[str]:
    return [note.lyric for note in notes if str(note.lyric) not in ["nan", "None"]]


