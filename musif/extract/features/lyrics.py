from typing import List

from music21.note import Note
from music21.stream import Part
from musif.config import Configuration

from musif.musicxml import contains_text, get_notes_lyrics


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:

    part = part_data["part"]
    notes = part_data["notes"]
    syllabic_ratio = get_syllabic_ratio(part, notes)

    return {
        "Syllabic ratio": syllabic_ratio,
    }


def get_syllabic_ratio(part: Part, notes: List[Note]) -> float:
    if not contains_text(part):
        return 0.0
    return len(notes) / len(get_notes_lyrics(notes))


