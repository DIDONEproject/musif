from typing import List

from music21.note import Note

from musif.common.constants import VOICE_FAMILY
from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.constants import DATA_FAMILY, DATA_PARTS_FILTER, DATA_PART_ABBREVIATION
from musif.extract.features.core import DATA_LYRICS, DATA_NOTES
from musif.extract.features.prefix import get_part_prefix, get_score_prefix

SYLLABIC_RATIO = "SyllabicRatio"
NOTES = "Notes"
SYLLABLES = "Syllables"


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):

    notes = part_data[DATA_NOTES]
    lyrics = part_data[DATA_LYRICS]

    syllabic_ratio = get_syllabic_ratio(notes, lyrics)

    part_features.update({
        NOTES: len(notes),
        SYLLABLES: len(lyrics),
        SYLLABIC_RATIO: syllabic_ratio,
    })


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    parts_data = filter_parts_data(parts_data, score_data[DATA_PARTS_FILTER])
    if len(parts_data) == 0:
        return

    voice_parts_data = [part_data for part_data in parts_data if part_data[DATA_FAMILY] == VOICE_FAMILY]

    features = {}
    for part_data in voice_parts_data:
        part_prefix = get_part_prefix(part_data[DATA_PART_ABBREVIATION])
        features[f"{part_prefix}{NOTES}"] = len(part_data[DATA_NOTES])
        features[f"{part_prefix}{SYLLABLES}"] = len(part_data[DATA_LYRICS])
        features[f"{part_prefix}{SYLLABIC_RATIO}"] = get_syllabic_ratio(part_data[DATA_NOTES], part_data[DATA_LYRICS])

    notes = [note for part_data in voice_parts_data for note in part_data[DATA_NOTES]]
    lyrics = [lyrics for part_data in voice_parts_data for lyrics in part_data[DATA_LYRICS]]

    score_prefix = get_score_prefix()
    features[f"{score_prefix}{NOTES}"] = len(notes)
    features[f"{score_prefix}{SYLLABLES}"] = len(lyrics)
    features[f"{score_prefix}{SYLLABIC_RATIO}"] = get_syllabic_ratio(notes, lyrics)

    return score_features.update(features)


def get_syllabic_ratio(notes: List[Note], lyrics: List[str]) -> float:
    if lyrics is None or len(lyrics) == 0:
        return 0.0
    return len(notes) / len(lyrics)


