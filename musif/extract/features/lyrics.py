from typing import List

from music21.note import Note
from music21.stream import Part

from musif.musicxml import contains_text, get_notes_lyrics


def get_single_part_features(part: Part, notes: List[Note]) -> dict:

    syllabic_ratio = get_syllabic_ratio(part, notes)

    return {
        "Syllabic ratio": syllabic_ratio,
    }


def get_syllabic_ratio(part: Part, notes: List[Note]) -> float:
    if not contains_text(part):
        return 0.0
    return len(notes) / len(get_notes_lyrics(notes))


