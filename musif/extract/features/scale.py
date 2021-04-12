from collections import Counter
from typing import List

from music21.note import Note

from musif.config import Configuration
from musif.musicxml import get_degrees_and_accidentals

accidental_abbreviation = {"": "", "sharp": "#", "flat": "b", "double-sharp": "x", "double-flat": "bb"}


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:
    notes = part_data["notes"]
    tonality = score_data["tonality"]
    notes_degrees = get_notes_degrees(tonality.capitalize(), notes)
    return Counter(notes_degrees)


def get_notes_degrees(key: str, notes: List[Note], prefix: str = "") -> List[str]:
    degrees_and_accidentals = get_degrees_and_accidentals(key, notes)
    note_degrees = [f"{prefix}Degree{accidental_abbreviation[accidental]}{degree}Frequency" for degree, accidental in degrees_and_accidentals]
    return note_degrees


