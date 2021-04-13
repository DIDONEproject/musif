from typing import List

from music21.note import Note

from musif.config import Configuration
from musif.extract.features.prefix import get_part_prefix

SYLLABIC_RATIO = "SyllabicRatio"
NOTES = "Notes"
LYRICS = "Lyrics"


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:

    notes = part_data["notes"]
    lyrics = part_data["lyrics"]

    syllabic_ratio = get_syllabic_ratio(notes, lyrics)

    features = {
        NOTES: len(notes),
        LYRICS: len(lyrics),
        SYLLABIC_RATIO: syllabic_ratio,
    }

    return features


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:

    notes = [note for part_data in parts_data for note in part_data["notes"]]
    lyrics = [lyrics for part_data in parts_data for lyrics in part_data["lyrics"]]

    syllabic_ratio = get_syllabic_ratio(notes, lyrics)

    features = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part_prefix = get_part_prefix(part_data["abbreviation"])
        for feature_name in (NOTES, LYRICS, SYLLABIC_RATIO):
            features[f"{part_prefix}{feature_name}"] = part_features[feature_name]

    features[NOTES] = len(notes)
    features[LYRICS] = len(lyrics)
    features[SYLLABIC_RATIO] = syllabic_ratio

    return features


def get_corpus_features(scores_data: List[dict], parts_data: List[dict], cfg: Configuration, scores_features: List[dict], corpus_features: dict) -> dict:

    features = {}
    grouped_parts_data = {}
    for part_data in parts_data:
        abb = part_data["abbreviation"]
        if abb not in grouped_parts_data:
            grouped_parts_data[abb] = {"notes": [], "lyrics": []}
        grouped_parts_data[abb]["notes"].extend(part_data["notes"])
        grouped_parts_data[abb]["lyrics"].extend(part_data["lyrics"])
    for abbreviation, grouped_part_data in grouped_parts_data.items():
        part_prefix = get_part_prefix(abbreviation)
        notes = grouped_part_data["notes"]
        lyrics = grouped_part_data["lyrics"]
        if len(lyrics) > 0:
            features[f"{part_prefix}{SYLLABIC_RATIO}"] = get_syllabic_ratio(notes, lyrics)
    return features


def get_syllabic_ratio(notes: List[Note], lyrics: List[str]) -> float:
    if not lyrics or len(lyrics) == 0:
        return 0.0
    return len(notes) / len(lyrics)


