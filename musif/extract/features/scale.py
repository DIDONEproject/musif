from typing import List, Dict, Union

from music21.note import Note

from musif.extract.constants import DATA_PARTS_FILTER, DATA_PART_ABBREVIATION
from musif.extract.features.core import DATA_TONALITY, DATA_NOTES
from musif.extract.features.prefix import get_part_prefix

from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.musicxml import get_degrees_and_accidentals

accidental_abbreviation = {"": "", "sharp": "#", "flat": "b", "double-sharp": "x", "double-flat": "bb"}

DEGREE_COUNT = "{prefix}Degree{key}_Count"
DEGREE_PER = "{prefix}Degree{key}_Per"


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    notes = part_data[DATA_NOTES]
    tonality = score_data[DATA_TONALITY]
    notes_per_degree = get_notes_per_degree(tonality.capitalize(), notes)
    all_degrees = sum(value for value in notes_per_degree.values())
    for key, value in notes_per_degree.items():
        part_features[DEGREE_COUNT.format(key=key, prefix="")] = value
        part_features[DEGREE_PER.format(key=key, prefix="")] = value / all_degrees if all_degrees != 0 else 0


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):
    parts_data = filter_parts_data(parts_data, score_data[DATA_PARTS_FILTER])
    if len(parts_data) == 0:
        return

    for part_data, parts_features in zip(parts_data, parts_features):
        part_prefix = get_part_prefix(part_data[DATA_PART_ABBREVIATION])
        for feature in parts_features:
            if "Degree" in feature:
                score_features[f"{part_prefix}{feature}"] = parts_features[feature]


def get_notes_per_degree(key: str, notes: List[Note]) -> Dict[str, int]:
    notes_per_degree = {
        to_full_degree(degree, accidental): 0
        for accidental in ["", "sharp", "flat"]
        for degree in [1, 2, 3, 4, 5, 6, 7]
    }
    all_degrees = 0
    for degree, accidental in get_degrees_and_accidentals(key, notes):
        if to_full_degree(degree, accidental) not in notes_per_degree:
            continue
        notes_per_degree[to_full_degree(degree, accidental)] += 1
        all_degrees += 1
    return notes_per_degree


def to_full_degree(degree: Union[int, str], accidental: str) -> str:
    return f"{accidental_abbreviation[accidental]}{degree}"

