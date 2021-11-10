from typing import List

from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.constants import DATA_PART, DATA_PARTS_FILTER, DATA_PART_ABBREVIATION
from musif.extract.features.prefix import get_part_prefix
from musif.musicxml.ambitus import get_part_ambitus
from .constants import *


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    part = part_data[DATA_PART]
    this_aria_ambitus, ambitus_pitch_span = get_part_ambitus(part)
    lowest_note, highest_note = ambitus_pitch_span
    lowest_note_text = lowest_note.nameWithOctave.replace("-", "b")
    highest_note_text = highest_note.nameWithOctave.replace("-", "b")
    lowest_note_index = int(lowest_note.ps)
    highest_note_index = int(highest_note.ps)

    ambitus_features = {
        LOWEST_NOTE: lowest_note_text,
        HIGHEST_NOTE: highest_note_text,
        LOWEST_NOTE_INDEX: lowest_note_index,
        HIGHEST_NOTE_INDEX: highest_note_index,
    }
    part_features.update(ambitus_features)


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    parts_data = filter_parts_data(parts_data, score_data[DATA_PARTS_FILTER])
    if len(parts_data) == 0:
        return

    for part_data, part_features in zip(parts_data, parts_features):
        part_prefix = get_part_prefix(part_data[DATA_PART_ABBREVIATION])
        for feature_name in SCORE_FEATURES:
            score_features[f"{part_prefix}{feature_name}"] = part_features[feature_name]
