from typing import List

from music21.note import Note

from musif.config import Configuration
from musif.extract.features.prefix import get_part_prefix, get_score_prefix

SYLLABIC_RATIO = "SyllabicRatio"


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:

    notes = part_data["notes"]
    lyrics = part_data["lyrics"]

    syllabic_ratio = get_syllabic_ratio(notes, lyrics)
    part_prefix = get_part_prefix(part_data["abbreviation"])

    return {
        f"{part_prefix}{SYLLABIC_RATIO}": syllabic_ratio,
    }


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:

    notes = [note for part_data in parts_data for note in part_data["notes"] if len(part_data["lyrics"]) > 0]
    lyrics = [lyrics for part_data in parts_data for lyrics in part_data["lyrics"] if len(part_data["lyrics"]) > 0]

    syllabic_ratio = get_syllabic_ratio(notes, lyrics)
    score_prefix = get_score_prefix()

    features = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part_prefix = get_part_prefix(part_data["abbreviation"])
        if len(part_data["lyrics"]) > 0:
            features[f"{part_prefix}{SYLLABIC_RATIO}"] = part_features[f"{part_prefix}{SYLLABIC_RATIO}"]
    features[f"{score_prefix}{SYLLABIC_RATIO}"] = syllabic_ratio

    return features


def get_syllabic_ratio(notes: List[Note], lyrics: List[str]) -> float:
    if not lyrics or len(lyrics) == 0:
        return 0.0
    return len(notes) / len(lyrics)


