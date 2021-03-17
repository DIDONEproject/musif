from typing import List, Optional, Tuple

from music21 import text
from music21.stream import Part, Score
from roman import toRoman

from musif.common.constants import VOICE_FAMILY
from musif.common.sort import sort
from musif.common.translate import translate_word
from musif.config import Configuration

ROMAN_NUMERALS_FROM_1_TO_20 = [toRoman(i).upper() for i in range(1, 21)]


def get_scoring_features(score: Score, config: Configuration) -> Tuple[dict, dict]:
    mapping = {}
    abbreviated_parts = []
    sounds = []
    families = []
    for part in score.parts:
        sound = extract_sound(part, config)
        abbreviated_part = extract_abbreviated_part(sound, part, score.parts, config)
        mapping[abbreviated_part] = part.partName
        abbreviated_parts.append(abbreviated_part)
        if sound not in sounds:
            sounds.append(sound)
        if sound in config.sound_to_family:
            family = config.sound_to_family[sound]
            if family not in families:
                families.append(family)

    abbreviated_parts_scoring_order = [instr + num
                                       for instr in config.scoring_order for num in [''] + ROMAN_NUMERALS_FROM_1_TO_20]
    sound_abbreviations = [config.sound_to_abbreviation[sound]
                           for sound in sounds if sound in config.sound_to_abbreviation]
    instrument_abbreviations = [config.sound_to_abbreviation[sound]
                                for sound in sounds if config.sound_to_family[sound] != VOICE_FAMILY and sound in config.sound_to_abbreviation]
    voice_abbreviations = [config.sound_to_abbreviation[sound]
                           for sound in sounds if config.sound_to_family[sound] == VOICE_FAMILY and sound in config.sound_to_abbreviation]
    family_abbreviations = [config.family_to_abbreviation[family]
                            for family in families if family in config.family_to_abbreviation]
    instrumental_families = [config.family_to_abbreviation[family]
                             for family in families if family not in VOICE_FAMILY and family in config.family_to_abbreviation]

    features = {
        "Scoring": ','.join(sort(abbreviated_parts, abbreviated_parts_scoring_order)),
        "SoundScoring": ','.join(sort(sound_abbreviations, config.scoring_order)),
        "Instrumentation": ','.join(sort(instrument_abbreviations, config.scoring_order)),
        "Voices": ','.join(sort(voice_abbreviations, config.scoring_order)),
        "FamilyScoring": ','.join(sort(family_abbreviations, config.scoring_family_order)),
        "FamilyInstrumentation": ','.join(sort(instrumental_families, config.scoring_family_order))
    }

    return features, mapping


def extract_sound(part: Part, config: Configuration) -> str:
    instrument = part.getInstrument(returnDefault=False)
    name = None
    if instrument is None or instrument.instrumentSound is None:
        name = translate_word(part.partName.strip().split(' ')[0], translations_cache=config.translations_cache)
        name = replace_naming_exceptions(name, part.partName)
        name = name if name[-1] != 's' else name[:-1]
    else:
        for instrument in instrument.instrumentSound.split('.')[::-1]:
            if 'flat' not in instrument and 'sharp' not in instrument and len(instrument) > 2:
                name = instrument
                break
    if name:
        name = name.replace('-', ' ').lower()
        name = translate_word(name, translations_cache=config.translations_cache)
        name = replace_naming_exceptions(name, part.partName)
    return name


def extract_abbreviated_part(sound: str, part: Part, parts: List[Part], config: Configuration) -> str:
    if sound not in config.sound_to_abbreviation:
        abbreviation = part.partAbbreviation  # may contain I and II
        abbreviation_parts = abbreviation.split(' ')
        abbreviation = abbreviation_parts[0].lower().replace('.', '') + (abbreviation_parts[1] if len(abbreviation_parts) > 1 else '')
    else:
        abbreviation = config.sound_to_abbreviation[sound]
    part_roman_number = extract_part_roman_number(part) or extract_part_roman_number_by_position(part, parts)
    return abbreviation + (part_roman_number or '')


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


def replace_naming_exceptions(sound: str, part: str) -> str:
    if 'da caccia' in sound:
        sound = sound.replace('da caccia', '')
        if 'tromba' in sound:
            sound = 'horn'
    if 'bass' == sound:  # determines if voice or string instrument
        if not text.assembleLyrics(part):
            sound = 'basso continuo'
    if 'french' in sound and 'horn' in sound:
        sound = 'horn'
    if 'cello' in sound and 'bass' in part.lower():
        sound = 'basso continuo'
    return sound


