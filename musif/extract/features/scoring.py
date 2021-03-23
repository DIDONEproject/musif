from copy import deepcopy
from typing import List, Optional, Tuple

from music21 import text
from music21.stream import Part
from roman import fromRoman, toRoman

from musif.common.constants import VOICE_FAMILY
from musif.common.sort import sort
from musif.common.translate import translate_word
from musif.config import Configuration

ROMAN_NUMERALS_FROM_1_TO_20 = [toRoman(i).upper() for i in range(1, 21)]


def get_single_part_features(part: Part, parts: List[Part], cfg: Configuration) -> dict:
    sound = extract_sound(part, cfg)
    part_abbreviation, sound_abbreviation, part_number = extract_abbreviated_part(sound, part, parts, cfg)
    family = cfg.sound_to_family[sound]
    family_abbreviation = cfg.family_to_abbreviation[family]
    instrumental = family != VOICE_FAMILY
    return {
        "PartName": part.partName,
        "PartNumber": part_number,
        "PartAbbreviation": part_abbreviation,
        "Sound": sound,
        "SoundAbbreviation": sound_abbreviation,
        "Family": family,
        "FamilyAbbreviation": family_abbreviation,
        "Instrumental": instrumental,
    }


def get_aggregated_parts_features(parts_features: List[dict]) -> List[dict]:
    parts_features = deepcopy(parts_features)
    count_by_sound = {}
    for features in parts_features:
        sound = features["Sound"]
        if sound not in count_by_sound:
            count_by_sound[sound] = 0
        count_by_sound[sound] += 1
    for features in parts_features:
        sound = features["Sound"]
        features["SoundCardinality"] = count_by_sound[sound]
    return parts_features


def get_global_features(parts_features: List[dict], cfg: Configuration) -> dict:
    abbreviated_parts = []
    sounds = []
    sound_abbreviations = []
    instrument_abbreviations = []
    voice_abbreviations = []
    families = []
    family_abbreviations = []
    instrumental_family_abbreviations = []
    for features in parts_features:
        sound = features["Sound"]
        sound_abbreviation = features["SoundAbbreviation"]
        abbreviated_part = features["PartAbbreviation"]
        abbreviated_parts.append(abbreviated_part)
        if sound not in sounds:
            sounds.append(sound)
            sound_abbreviations.append(sound_abbreviation)
            if features["Instrumental"]:
                instrument_abbreviations.append(sound_abbreviation)
            else:
                voice_abbreviations.append(sound_abbreviation)
        family = features["Family"]
        family_abbreviation = features["FamilyAbbreviation"]
        if family not in families:
            families.append(family)
            family_abbreviations.append(family_abbreviation)
            if features["Instrumental"]:
                instrumental_family_abbreviations.append(family_abbreviation)

    abbreviated_parts_scoring_order = [instr + num
                                       for instr in cfg.scoring_order for num in [''] + ROMAN_NUMERALS_FROM_1_TO_20]
    return {
        "Scoring": ','.join(sort(abbreviated_parts, abbreviated_parts_scoring_order)),
        "SoundScoring": ','.join(sort(sound_abbreviations, cfg.scoring_order)),
        "Instrumentation": ','.join(sort(instrument_abbreviations, cfg.scoring_order)),
        "Voices": ','.join(sort(voice_abbreviations, cfg.scoring_order)),
        "FamilyScoring": ','.join(sort(family_abbreviations, cfg.scoring_family_order)),
        "FamilyInstrumentation": ','.join(sort(instrumental_family_abbreviations, cfg.scoring_family_order)),
        "PartsCardinality": len(parts_features),
        "ScoringCardinality": len(parts_features),
    }


def to_abbreviation(part: Part, parts: List[Part], cfg: Configuration) -> str:
    sound = extract_sound(part, cfg)
    return extract_abbreviated_part(sound, part, parts, cfg)[0]


def extract_sound(part: Part, config: Configuration) -> str:
    instrument = part.getInstrument(returnDefault=False)
    sound_name = None
    if instrument is None or instrument.instrumentSound is None:
        sound_name = part.partName.strip().split(' ')[0]
        if sound_name not in config.sound_to_abbreviation:
            sound_name = translate_word(sound_name, translations_cache=config.translations_cache)
            sound_name = replace_naming_exceptions(sound_name, part.partName)
            sound_name = sound_name if sound_name[-1] != 's' else sound_name[:-1]
    else:
        for instrument in instrument.instrumentSound.split('.')[::-1]:
            if 'flat' not in instrument and 'sharp' not in instrument and len(instrument) > 2:
                sound_name = instrument
                break
    if sound_name:
        sound_name = sound_name.replace('-', ' ').lower()
        sound_name = replace_naming_exceptions(sound_name, part.partName)
    return sound_name


def extract_abbreviated_part(sound: str, part: Part, parts: List[Part], config: Configuration) -> Tuple[str, str, int]:
    if sound not in config.sound_to_abbreviation:
        abbreviation = part.partAbbreviation  # may contain I, II or whatever
        abbreviation_parts = abbreviation.split(' ')
        abbreviation = abbreviation_parts[0].lower().replace('.', '') + (abbreviation_parts[1] if len(abbreviation_parts) > 1 else '')
    else:
        abbreviation = config.sound_to_abbreviation[sound]
    part_roman_number = extract_part_roman_number(part) or extract_part_roman_number_by_position(part, parts)
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


