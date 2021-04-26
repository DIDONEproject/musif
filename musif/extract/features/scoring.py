from typing import List, Optional, Tuple

from statistics import mean, stdev
from music21 import text
from music21.stream import Part
from roman import fromRoman, toRoman

from musif.common.constants import VOICE_FAMILY
from musif.common.sort import sort
from musif.common.translate import translate_word
from musif.config import Configuration
from musif.extract.features.prefix import get_family_prefix, get_sound_prefix, get_corpus_prefix

ROMAN_NUMERALS_FROM_1_TO_20 = [toRoman(i).upper() for i in range(1, 21)]

PART_NAME = "PartName"
PART_NUMBER = "PartNumber"
PART_ABBREVIATION = "PartAbbreviation"
SOUND = "Sound"
SOUND_ABBREVIATION = "SoundAbbreviation"
FAMILY = "Family"
FAMILY_ABBREVIATION = "FamilyAbbreviation"
INSTRUMENTAL = "Instrumental"
CARDINALITY = "Cardinality"
SCORING = "Scoring"
SOUND_SCORING = "SoundScoring"
INSTRUMENTATION = "Instrumentation"
VOICES = "Voices"
FAMILY_SCORING = "FamilyScoring"
FAMILY_INSTRUMENTATION = "FamilyInstrumentation"
CARDINALITY_MEAN = "CardinalityMean"
CARDINALITY_STD = "CardinalityStd"


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:
    part = part_data["part"]
    instrumental = part_data["family"] != VOICE_FAMILY
    return {
        PART_NAME: part.partName,
        PART_NUMBER: part_data["part_number"],
        PART_ABBREVIATION: part_data["abbreviation"],
        SOUND: part_data["sound"],
        SOUND_ABBREVIATION: part_data["sound_abbreviation"],
        FAMILY: part_data["family"],
        FAMILY_ABBREVIATION: part_data["family_abbreviation"],
        INSTRUMENTAL: instrumental,
    }


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    abbreviated_parts = []
    sounds = []
    sound_abbreviations = []
    instrument_abbreviations = []
    voice_abbreviations = []
    families = []
    family_abbreviations = []
    instrumental_family_abbreviations = []
    count_by_sound = {}
    count_by_family = {}
    for features in parts_features:
        part = features[PART_ABBREVIATION]
        sound = features[SOUND]
        sound_abbreviation = features[SOUND_ABBREVIATION]
        family = features[FAMILY]
        family_abbreviation = features[FAMILY_ABBREVIATION]
        abbreviated_parts.append(part)
        if sound_abbreviation not in count_by_sound:
            count_by_sound[sound_abbreviation] = 0
        count_by_sound[sound_abbreviation] += 1
        if family_abbreviation not in count_by_family:
            count_by_family[family_abbreviation] = 0
        count_by_family[family_abbreviation] += 1
        if sound not in sounds:
            sounds.append(sound)
            sound_abbreviations.append(sound_abbreviation)
            if features[INSTRUMENTAL]:
                instrument_abbreviations.append(sound_abbreviation)
            else:
                voice_abbreviations.append(sound_abbreviation)
        if family not in families:
            families.append(family)
            family_abbreviations.append(family_abbreviation)
            if features[INSTRUMENTAL]:
                instrumental_family_abbreviations.append(family_abbreviation)

    abbreviated_parts_scoring_order = [instr + num
                                       for instr in cfg.scoring_order for num in [''] + ROMAN_NUMERALS_FROM_1_TO_20]
    features = {
        SCORING: ','.join(sort(abbreviated_parts, abbreviated_parts_scoring_order)),
        SOUND_SCORING: ','.join(sort(sound_abbreviations, cfg.scoring_order)),
        INSTRUMENTATION: ','.join(sort(instrument_abbreviations, cfg.scoring_order)),
        VOICES: ','.join(sort(voice_abbreviations, cfg.scoring_order)),
        FAMILY_SCORING: ','.join(sort(family_abbreviations, cfg.scoring_family_order)),
        FAMILY_INSTRUMENTATION: ','.join(sort(instrumental_family_abbreviations, cfg.scoring_family_order)),
        CARDINALITY: len(parts_features),
    }
    for sound_abbreviation in sound_abbreviations:
        sound_prefix = get_sound_prefix(sound_abbreviation)
        features[f"{sound_prefix}{CARDINALITY}"] = count_by_sound[sound_abbreviation]
    for family_abbreviation in family_abbreviations:
        family_prefix = get_family_prefix(family_abbreviation)
        features[f"{family_prefix}{CARDINALITY}"] = count_by_family[family_abbreviation]

    return features


def get_corpus_features(scores_data: List[dict], parts_data: List[dict], cfg: Configuration, scores_features: List[dict], corpus_features: dict) -> dict:

    abbreviated_parts = list({part for score_features in scores_features for part in score_features[SCORING].split(',')})
    abbreviated_parts_scoring_order = [instr + num for instr in cfg.scoring_order for num in [''] + ROMAN_NUMERALS_FROM_1_TO_20]
    sound_abbreviations = list({sound for score_features in scores_features for sound in score_features[SOUND_SCORING].split(',')})
    instrument_abbreviations = list({instrument for score_features in scores_features for instrument in score_features[INSTRUMENTATION].split(',')})
    voice_abbreviations = list({voice for score_features in scores_features for voice in score_features[VOICES].split(',')})
    family_abbreviations = list({family for score_features in scores_features for family in score_features[FAMILY_SCORING].split(',')})
    instrumental_family_abbreviations = list({family for score_features in scores_features for family in score_features[FAMILY_INSTRUMENTATION].split(',')})
    scoring_count_mean = mean([score_features[CARDINALITY] for score_features in scores_features])
    scoring_count_std = stdev([score_features[CARDINALITY] for score_features in scores_features]) if len(scores_features) > 1 else 0
    corpus_prefix = get_corpus_prefix()
    features = {
        f"{corpus_prefix}{SCORING}": ','.join(sort(abbreviated_parts, abbreviated_parts_scoring_order)),
        f"{corpus_prefix}{SOUND_SCORING}": ','.join(sort(sound_abbreviations, cfg.scoring_order)),
        f"{corpus_prefix}{INSTRUMENTATION}": ','.join(sort(instrument_abbreviations, cfg.scoring_order)),
        f"{corpus_prefix}{VOICES}": ','.join(sort(voice_abbreviations, cfg.scoring_order)),
        f"{corpus_prefix}{FAMILY_SCORING}": ','.join(sort(family_abbreviations, cfg.scoring_family_order)),
        f"{corpus_prefix}{FAMILY_INSTRUMENTATION}": ','.join(sort(instrumental_family_abbreviations, cfg.scoring_family_order)),
        f"{corpus_prefix}{CARDINALITY_MEAN}": scoring_count_mean,
        f"{corpus_prefix}{CARDINALITY_STD}": scoring_count_std,
    }
    return features


def to_abbreviation(part: Part, parts: List[Part], cfg: Configuration) -> str:
    sound = extract_sound(part, cfg)
    return extract_abbreviated_part(sound, part, parts, cfg)[0]


def extract_sound(part: Part, config: Configuration) -> str:
    instrument = part.getInstrument(returnDefault=False)
    sound_name = None
    if instrument is None or instrument.instrumentSound is None:
        sound_name = part.partName.strip().split(' ')[0]
        if sound_name not in config.sound_to_abbreviation:
            sound_name = translate_word(
                sound_name, translations_cache=config.translations_cache)
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
