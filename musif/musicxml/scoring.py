from typing import List, Optional, Tuple

from music21.stream import Part
from roman import fromRoman, toRoman

from musif.common.translate import translate_word
from musif.config import Configuration

ROMAN_NUMERALS_FROM_1_TO_20 = [toRoman(i).upper() for i in range(1, 21)]

# TODO: document this module

def to_abbreviation(part: Part, parts: List[Part], cfg: Configuration) -> str:
    sound = extract_sound(part, cfg)
    return list(extract_abbreviated_part(sound, part, parts, cfg))[0]


def extract_sound(part: Part, config: Configuration) -> str:
    instrument = part.getInstrument(returnDefault=False)
    sound_name = None
    if instrument is None or instrument.instrumentSound is None:
        sound_name = part.partName.strip().split(' ')[0]
        if sound_name not in config.sound_to_abbreviation:
            sound_name = translate_word(
                sound_name, translations_cache=config.translations_cache)
            sound_name = replace_naming_exceptions(sound_name, part)
            sound_name = sound_name if sound_name[-1] != 's' else sound_name[:-1]
    else:
        for instrument in instrument.instrumentSound.split('.')[::-1]:
            if 'flat' not in instrument and 'sharp' not in instrument and len(instrument) > 2:
                sound_name = instrument
                break
    if sound_name:
        sound_name = sound_name.replace('-', ' ').lower()
        sound_name = replace_naming_exceptions(sound_name, part)
    return sound_name


def extract_abbreviated_part(sound: str, part: Part, parts: List[Part], config: Configuration) -> Tuple[str, str, int]:
    if sound not in config.sound_to_abbreviation:
        abbreviation = part.partAbbreviation  # may contain I, II or whatever
        abbreviation_parts = abbreviation.split(' ')
        abbreviation = abbreviation_parts[0].lower().replace(
            '.', '') + (abbreviation_parts[1] if len(abbreviation_parts) > 1 else '')
    else:
        abbreviation = config.sound_to_abbreviation[sound]
    part_roman_number = extract_part_roman_number(
        part) or extract_part_roman_number_by_position(part, parts)
    part_number = fromRoman(part_roman_number) if part_roman_number else 0
    return abbreviation + (part_roman_number or ''), abbreviation, part_number


def extract_part_roman_number(part: Part) -> Optional[str]:
    for number in ROMAN_NUMERALS_FROM_1_TO_20:
        if part.partAbbreviation.endswith(f'. {number}') or part.partName.endswith(f' {number}'):
            return number
    return None


def extract_part_roman_number_by_position(part: Part, parts: List[Part]) -> Optional[str]:
    same_sound_parts = [same_sound_part
                        for same_sound_part in parts
                        if part.getInstrument(returnDefault=False) == same_sound_part.getInstrument(returnDefault=False)]
    if len(same_sound_parts) > 1:
        for i, same_sound_part in enumerate(same_sound_parts, 1):
            if part.partName == same_sound_part.partName:
                return toRoman(i)
    return None


# TODO: these exceptions should stay in some configuration?
def replace_naming_exceptions(sound: str, part: Part) -> str:
    if 'da caccia' in sound:
        sound = sound.replace('da caccia', '')
        if 'tromba' in sound:
            sound = 'horn'
    if 'bass' == sound:  # determines if voice or string instrument
        if len(part.lyrics()) == 0:
            sound = 'basso continuo'
    if 'french' in sound and 'horn' in sound:
        sound = 'horn'
    if 'cello' in sound and 'bass' in part.partName.lower():
        sound = 'basso continuo'
    return sound
