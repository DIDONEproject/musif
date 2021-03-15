from typing import Optional, Tuple

import roman
from music21.stream import Part

from config import family_to_abbreviation, sound_to_abbreviation
from musif.features.score.melody.scoring import ROMAN_NUMERALS_FROM_1_TO_20, VOICE_FAMILY


def extract_instrument_and_number_from_part(part: str) -> Tuple[str, Optional[str]]:
    for i in range(100, 0, -1):
        number = roman.toRoman(i)
        number_index = part.rfind(number)
        if number_index >= 0:
            return part[:number_index].strip(), part[number_index:].strip()
    return part, None


def to_part_name(instrument: str, number: Optional[str] = None) -> str:
    return instrument + (f' ({number})' if number else '')


def score_part_to_family_and_instrument(score_part: Part) -> Tuple[str, str]:
    family, instrument = score_part.getInstrument(returnDefault=False).instrumentSound.split('.')
    return family, instrument


def extract_part_roman_number(score_part: Part) -> Optional[str]:
    for number in ROMAN_NUMERALS_FROM_1_TO_20:
        if score_part.partAbbreviation.endswith(f'. {number}'):
            return number
    return None


def score_part_to_part_instrument(score_part: Part) -> str:
    family, instrument = score_part_to_family_and_instrument(score_part)
    if family == VOICE_FAMILY:
        return to_part_name(family_to_abbreviation[family])
    part_number = extract_part_roman_number(score_part)
    abbreviation = sound_to_abbreviation[instrument]
    return to_part_name(abbreviation, part_number)
