from typing import List

from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.constants import DATA_PART_ABBREVIATION
from musif.musicxml.ambitus import get_notes_ambitus
from .constants import *
from ..core.constants import DATA_NOTES
from ..prefix import get_part_feature


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    notes = part_data[DATA_NOTES]
    if notes is None or len(notes) == 0:

        return
    lowest_note, highest_note = get_notes_ambitus(notes)
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
        AMBITUS: total_ambitus
    }
    part_features.update(ambitus_features)


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    parts_data = filter_parts_data(parts_data, cfg.parts_filter)
    if len(parts_data) == 0:
        return

    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]
        for feature_name in SCORE_FEATURES:
            score_features[get_part_feature(part, feature_name)] = part_features.get(feature_name)
