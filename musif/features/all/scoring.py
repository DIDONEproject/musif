from typing import List, Optional, Tuple, Dict, Set

from music21 import text
from music21.stream import Part, Score
from roman import toRoman

from musif.common.sort import sort
from musif.common.translate import translate_word
from musif.config import family_to_abbreviation, scoring_family_order, scoring_order, sound_to_abbreviation, sound_to_family

ROMAN_NUMERALS_FROM_1_TO_20 = [toRoman(i).upper() for i in range(1, 21)]
ABBREVIATED_PARTS_SCORING_ORDER = [instr + num for instr in scoring_order for num in [''] + ROMAN_NUMERALS_FROM_1_TO_20]
VOICE_FAMILY = 'voice'
STR_SOUND_GROUPS = [{'violin', 'viola', 'basso continuo'}, {'violin', 'viola', 'cello'}]


def get_scoring_features(score: Score) -> Tuple[dict, dict]:
    mapping = {}
    abbreviated_parts = []
    sounds = []
    families = []
    for part in score.parts:
        sound = extract_sound(part)
        abbreviated_part = extract_abbreviated_part(sound, part, score.parts)
        mapping[abbreviated_part] = part.partName
        abbreviated_parts.append(abbreviated_part)
        if sound not in sounds:
            sounds.append(sound)
        if sound in sound_to_family:
            family = sound_to_family[sound]
            if family not in families:
                families.append(family)

    sound_abbreviations = [sound_to_abbreviation[sound] for sound in sounds if sound in sound_to_abbreviation]
    instrument_abbreviations = [sound_to_abbreviation[sound] for sound in sounds if sound_to_family[sound] != VOICE_FAMILY and sound in sound_to_abbreviation]
    voice_abbreviations = [sound_to_abbreviation[sound] for sound in sounds if sound_to_family[sound] == VOICE_FAMILY and sound in sound_to_abbreviation]
    family_abbreviations = [family_to_abbreviation[family] for family in families if family in family_to_abbreviation]
    instrumental_families = [family_to_abbreviation[family] for family in families if family not in VOICE_FAMILY and family in family_to_abbreviation]

    features = {
        "Scoring": ','.join(sort(abbreviated_parts, ABBREVIATED_PARTS_SCORING_ORDER)),
        "SoundScoring": ','.join(sort(sound_abbreviations, scoring_order)),
        "Instrumentation": ','.join(sort(instrument_abbreviations, scoring_order)),
        "Voices": ','.join(sort(voice_abbreviations, scoring_order)),
        "FamilyScoring": ','.join(sort(family_abbreviations, scoring_family_order)),
        "FamilyInstrumentation": ','.join(sort(instrumental_families, scoring_family_order))
    }

    return features, mapping


def extract_sound(part: Part) -> str:
    instrument = part.getInstrument(returnDefault=False)
    name = None
    if instrument is None or instrument.instrumentSound is None:
        name = translate_word(part.partName.strip().split(' ')[0])
        name = replace_naming_exceptions(name, part.partName)
        name = name if name[-1] != 's' else name[:-1]
    else:
        for instrument in instrument.instrumentSound.split('.')[::-1]:
            if 'flat' not in instrument and 'sharp' not in instrument and len(instrument) > 2:
                name = instrument
                break
    if name:
        name = name.replace('-', ' ').lower()
        name = translate_word(name)
        name = replace_naming_exceptions(name, part.partName)
    return name


def extract_abbreviated_part(sound: str, part: Part, parts: List[Part]) -> str:
    if sound not in sound_to_abbreviation:
        abbreviation = part.partAbbreviation  # may contain I and II
        abbreviation_parts = abbreviation.split(' ')
        abbreviation = abbreviation_parts[0].lower().replace('.', '') + (abbreviation_parts[1] if len(abbreviation_parts) > 1 else '')
    else:
        abbreviation = sound_to_abbreviation[sound]
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


def get_matching_str_groups(sounds: List[str]) -> List[set]:
    my_sounds = set(sounds)
    str_groups = []
    for str_sounds_set in STR_SOUND_GROUPS:
        matching = True
        for str_sound in str_sounds_set:
            if str_sound not in my_sounds:
                matching = False
                break
        if matching:
            str_groups.append(str_sounds_set)
    return str_groups


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


def choose_score_parts(score: Score, parts_filter: Set[str], abbreviation_to_part: Dict[str, str]) -> List[Part]:
    chosen_score_part_names = {score_part_name for abbreviation, score_part_name in abbreviation_to_part.items() if abbreviation in parts_filter}
    return [part for part in score.parts if part.partName in chosen_score_part_names]

