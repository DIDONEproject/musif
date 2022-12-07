from statistics import mean
from typing import List, Optional, Tuple

from music21.chord import Chord
from music21.harmony import ChordSymbol

from music21.note import Note

from musif.config import ExtractConfiguration
from musif.extract.common import _filter_parts_data
from musif.extract.constants import DATA_PART_ABBREVIATION
from musif.extract.features.core.constants import DATA_NOTES
from musif.cache import isinstance

from ..prefix import get_part_feature
from .constants import *


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    notes = part_data[DATA_NOTES]
    if notes is None or len(notes) == 0:
        return
    lowest_note, highest_note = _get_notes_ambitus(notes)
    lowest_note_text = lowest_note.nameWithOctave.replace("-", "b")
    highest_note_text = highest_note.nameWithOctave.replace("-", "b")
    lowest_note_index = int(lowest_note.pitch.midi)
    highest_note_index = int(highest_note.pitch.midi)
    total_ambitus = highest_note_index - lowest_note_index
    ambitus_features = {
        LOWEST_NOTE: lowest_note_text,
        HIGHEST_NOTE: highest_note_text,
        LOWEST_NOTE_INDEX: lowest_note_index,
        HIGHEST_NOTE_INDEX: highest_note_index,
        AMBITUS: total_ambitus,
    }
    part_features.update(ambitus_features)


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):

    parts_data = _filter_parts_data(parts_data, cfg.parts_filter)
    if len(parts_data) == 0:
        return

    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]
        for feature_name in SCORE_FEATURES:
            part_feature = get_part_feature(part, feature_name)
            if feature_name in score_features:
                score_features[part_feature] = mean(
                    [score_features[part_feature], parts_features[feature_name]]
                )
            else:
                score_features[part_feature] = part_features.get(feature_name)


def _get_notes_ambitus(notes: List[Note]) -> Tuple[Note, Note]:
    first_note = notes[0][0] if isinstance(notes[0], (Chord, ChordSymbol)) else notes[0]
    lowest_note = first_note
    highest_note = first_note
    for note in notes[1:]:
        current_note = note[0] if isinstance(note, (Chord, ChordSymbol)) else note
        if current_note.pitch.midi < lowest_note.pitch.midi:
            lowest_note = current_note
        if current_note.pitch.midi > highest_note.pitch.midi:
            highest_note = current_note
    return lowest_note, highest_note
