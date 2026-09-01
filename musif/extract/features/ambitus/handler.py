from typing import List, Optional, Tuple

from music21.chord import Chord
from music21.harmony import ChordSymbol

from music21.note import Note

from musif.config import ExtractConfiguration
from musif.extract.common import _filter_parts_data
from musif.extract.constants import (
    DATA_FAMILY_ABBREVIATION,
    DATA_PART_ABBREVIATION,
    DATA_SOUND_ABBREVIATION,
)
from musif.extract.features.core.constants import DATA_NOTES
from musif.cache import isinstance

from ..prefix import (
    get_family_feature,
    get_part_feature,
    get_score_feature,
    get_sound_feature,
)
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

    # Aggregate extremes per part (staves sharing an abbreviation merge into
    # one logical part), per sound, per family, and for the whole score:
    # min of lowest notes, max of highest, difference for the ambitus.
    part_extremes = {}
    sound_extremes = {}
    family_extremes = {}
    score_extremes = None

    for part_data, part_features in zip(parts_data, parts_features):
        if HIGHEST_NOTE_INDEX not in part_features:
            continue  # the part had no notes
        extremes = (
            part_features[LOWEST_NOTE_INDEX],
            part_features[LOWEST_NOTE],
            part_features[HIGHEST_NOTE_INDEX],
            part_features[HIGHEST_NOTE],
        )
        _merge_extremes(part_extremes, part_data[DATA_PART_ABBREVIATION], extremes)
        _merge_extremes(sound_extremes, part_data[DATA_SOUND_ABBREVIATION], extremes)
        _merge_extremes(family_extremes, part_data[DATA_FAMILY_ABBREVIATION], extremes)
        score_extremes = _merged(score_extremes, extremes)

    for part, extremes in part_extremes.items():
        _emit_extremes(score_features, lambda n: get_part_feature(part, n), extremes)
    for sound, extremes in sound_extremes.items():
        _emit_extremes(score_features, lambda n: get_sound_feature(sound, n), extremes)
    for family, extremes in family_extremes.items():
        _emit_extremes(
            score_features, lambda n: get_family_feature(family, n), extremes
        )
    if score_extremes is not None:
        _emit_extremes(score_features, get_score_feature, score_extremes)


def _merged(current, new):
    if current is None:
        return list(new)
    lo_i, lo_t, hi_i, hi_t = new
    if lo_i < current[0]:
        current[0], current[1] = lo_i, lo_t
    if hi_i > current[2]:
        current[2], current[3] = hi_i, hi_t
    return current


def _merge_extremes(store, key, new):
    store[key] = _merged(store.get(key), new)


def _emit_extremes(score_features, make_name, extremes):
    lo_i, lo_t, hi_i, hi_t = extremes
    score_features[make_name(LOWEST_NOTE)] = lo_t
    score_features[make_name(HIGHEST_NOTE)] = hi_t
    score_features[make_name(LOWEST_NOTE_INDEX)] = lo_i
    score_features[make_name(HIGHEST_NOTE_INDEX)] = hi_i
    score_features[make_name(AMBITUS)] = hi_i - lo_i


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
