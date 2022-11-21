from typing import Optional, Tuple

import roman
from music21.stream import Part

from musif.common.constants import VOICE_FAMILY
from musif.config import Configuration
from musif.musicxml.scoring import ROMAN_NUMERALS_FROM_1_TO_20

# TODO: document all these functions
# TODO: function names may be improved?

def get_instrument_name_and_number_from_part(part: str) -> Tuple[str, Optional[str]]:
    """
    Takes a music21 part object and returns the part name and the roman number corresponding
    to the specific part in case there is more than one instrument of the same name.
    
    Parameters
    ----------
        part : Part
      Music21 part to take the info from
    
    """
    for i in range(100, 0, -1):
        number = roman.toRoman(i)
        number_index = part.rfind(number)
        if number_index >= 0:
            return part[:number_index].strip(), part[number_index:].strip()
    return part, None


# def _part_to_part_instrument_name(part: Part, config: Configuration) -> str:
#     """
#     Takes a music21 part object and returns 
#     Parameters
#     ----------
#         part : Part
#       Music21 part to take the info from
    
#     """
#     family, instrument = _part_to_family_and_instrument_name(part)
#     if family == VOICE_FAMILY:
#         return _to_part_name(config.family_to_abbreviation[family])
#     part_number = _extract_part_roman_number(part)
#     abbreviation = config.sound_to_abbreviation[instrument]
#     return _to_part_name(abbreviation, part_number)


def _to_part_name(instrument: str, number: Optional[str] = None) -> str:
    return instrument + (f' ({number})' if number else '')


def _part_to_family_and_instrument_name(score_part: Part) -> Tuple[str, str]:
    family, instrument = score_part.getInstrument(returnDefault=False).instrumentSound.split('.')
    return family, instrument


def _extract_part_roman_number(part: Part) -> Optional[str]:
    for number in ROMAN_NUMERALS_FROM_1_TO_20:
        if part.partAbbreviation.endswith(f'. {number}'):
            return number
    return None


