from typing import List

from musif.common.constants import GENERAL_FAMILY, VOICE_FAMILY
from musif.common.sort import sort
from musif.config import Configuration
from musif.extract.common import part_matches_filter
from musif.extract.constants import DATA_FAMILY, DATA_FAMILY_ABBREVIATION, DATA_FILTERED_PARTS, DATA_PART, \
    DATA_PARTS_FILTER, DATA_PART_ABBREVIATION, DATA_PART_NUMBER, DATA_SCORE, DATA_SOUND, DATA_SOUND_ABBREVIATION
from musif.extract.features.prefix import get_family_prefix, get_sound_prefix
from musif.musicxml.scoring import ROMAN_NUMERALS_FROM_1_TO_20, extract_abbreviated_part, extract_sound
from .constants import *


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    part = part_data[DATA_PART]
    instrumental = part_data[DATA_FAMILY] != VOICE_FAMILY
    part_features.update({
        PART_NAME: part.partName,
        PART_NUMBER: part_data[DATA_PART_NUMBER],
        PART_ABBREVIATION: part_data[DATA_PART_ABBREVIATION],
        SOUND: part_data[DATA_SOUND],
        SOUND_ABBREVIATION: part_data[DATA_SOUND_ABBREVIATION],
        FAMILY: part_data[DATA_FAMILY],
        FAMILY_ABBREVIATION: part_data[DATA_FAMILY_ABBREVIATION],
        INSTRUMENTAL: instrumental,
    })


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):
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
    filtered_count_by_sound = {}
    filtered_count_by_family = {}
    score = score_data[DATA_SCORE]
    for part in score.parts:
        sound = extract_sound(part, cfg)
        part_abbreviation, sound_abbreviation, part_number = extract_abbreviated_part(
            sound, part, score_data[DATA_FILTERED_PARTS], cfg)
        is_matching_part = part_matches_filter(part_abbreviation, score_data[DATA_PARTS_FILTER])
        family = cfg.sound_to_family.get(sound, GENERAL_FAMILY)
        family_abbreviation = cfg.family_to_abbreviation[family]
        abbreviated_parts.append(part_abbreviation)
        instrumental = family != VOICE_FAMILY
        if sound_abbreviation not in count_by_sound:
            count_by_sound[sound_abbreviation] = 0
            filtered_count_by_sound[sound_abbreviation] = 0
        count_by_sound[sound_abbreviation] += 1
        filtered_count_by_sound[sound_abbreviation] += 1 if is_matching_part else 0
        if family_abbreviation not in count_by_family:
            count_by_family[family_abbreviation] = 0
            filtered_count_by_family[family_abbreviation] = 0
        count_by_family[family_abbreviation] += 1
        filtered_count_by_family[family_abbreviation] += 1 if is_matching_part else 0
        if sound not in sounds:
            sounds.append(sound)
            sound_abbreviations.append(sound_abbreviation)
            if instrumental:
                instrument_abbreviations.append(sound_abbreviation)
            else:
                voice_abbreviations.append(sound_abbreviation)
        if family not in families:
            families.append(family)
            family_abbreviations.append(family_abbreviation)
            if instrumental:
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
        NUMBER_OF_PARTS: len(abbreviated_parts),
    }
    for sound_abbreviation in sound_abbreviations:
        sound_prefix = get_sound_prefix(sound_abbreviation)
        features[f"{sound_prefix}{NUMBER_OF_PARTS}"] = count_by_sound[sound_abbreviation]
        features[f"{sound_prefix}{NUMBER_OF_FILTERED_PARTS}"] = filtered_count_by_sound[sound_abbreviation]
    for family_abbreviation in family_abbreviations:
        family_prefix = get_family_prefix(family_abbreviation)
        features[f"{family_prefix}{NUMBER_OF_PARTS}"] = count_by_family[family_abbreviation]
        features[f"{family_prefix}{NUMBER_OF_FILTERED_PARTS}"] = filtered_count_by_family[family_abbreviation]

    return score_features.update(features)
