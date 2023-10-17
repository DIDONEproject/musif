from typing import List

from musif.common._constants import GENERAL_FAMILY, VOICE_FAMILY
from musif.common.sort import sort_list
from musif.config import ExtractConfiguration
from musif.extract.common import _part_matches_filter
from musif.extract.constants import (
    DATA_FAMILY,
    DATA_FAMILY_ABBREVIATION,
    DATA_FILTERED_PARTS,
    DATA_PART,
    DATA_PART_ABBREVIATION,
    DATA_PART_NUMBER,
    DATA_SCORE,
    DATA_SOUND,
    DATA_SOUND_ABBREVIATION,
)
from musif.extract.features.prefix import (
    get_family_feature,
    get_family_prefix,
    get_score_feature,
    get_sound_feature,
    get_sound_prefix,
)
from musif.musicxml.scoring import (
    ROMAN_NUMERALS_FROM_1_TO_20,
    _extract_abbreviated_part,
    extract_sound,
)
from .constants import *


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    part = part_data[DATA_PART]
    instrumental = part_data[DATA_FAMILY] != VOICE_FAMILY
    part_features.update(
        {
            PART_NAME: part.partName,
            PART_NUMBER: part_data[DATA_PART_NUMBER],
            PART_ABBREVIATION: part_data[DATA_PART_ABBREVIATION],
            SOUND: part_data[DATA_SOUND],
            SOUND_ABBREVIATION: part_data[DATA_SOUND_ABBREVIATION],
            FAMILY: part_data[DATA_FAMILY],
            FAMILY_ABBREVIATION: part_data[DATA_FAMILY_ABBREVIATION],
            INSTRUMENTAL: instrumental,
        }
    )


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
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
        part_abbreviation, sound_abbreviation, part_number = _extract_abbreviated_part(
            sound, part, score_data[DATA_FILTERED_PARTS], cfg)
        is_matching_part = _part_matches_filter(part_abbreviation, cfg.parts_filter)
        family = cfg.sound_to_family.get(sound, GENERAL_FAMILY)
        family_abbreviation = cfg.family_to_abbreviation.get(family, family)
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
        if sound_abbreviation not in sound_abbreviations:
            sound_abbreviations.append(sound_abbreviation)
            if instrumental:
                instrument_abbreviations.append(sound_abbreviation)
        if not instrumental:
            voice_abbreviations.append(part_abbreviation)
        if family not in families:
            families.append(family)
            family_abbreviations.append(family_abbreviation)
            if instrumental:
                instrumental_family_abbreviations.append(family_abbreviation)

    abbreviated_parts_scoring_order = [
        instr + num
        for instr in cfg.scoring_order
        for num in [""] + ROMAN_NUMERALS_FROM_1_TO_20
    ]
    features = {
        SCORING: ",".join(
            sort_list(abbreviated_parts, abbreviated_parts_scoring_order)
        ),
        SOUND_SCORING: ",".join(sort_list(sound_abbreviations, cfg.scoring_order)),
        INSTRUMENTATION: ",".join(
            sort_list(instrument_abbreviations, cfg.scoring_order)
        ),
        VOICES: ",".join(sort_list(voice_abbreviations, cfg.scoring_order)),
        FAMILY_SCORING: ",".join(
            sort_list(family_abbreviations, cfg.scoring_family_order)
        ),
        FAMILY_INSTRUMENTATION: ",".join(
            sort_list(instrumental_family_abbreviations, cfg.scoring_family_order)
        ),
    }
    for sound in sound_abbreviations:
        features[get_sound_feature(sound, NUMBER_OF_PARTS)] = count_by_sound[sound]
        features[
            get_sound_feature(sound, NUMBER_OF_FILTERED_PARTS)
        ] = filtered_count_by_sound[sound]
        score_data[
            get_sound_feature(sound, NUMBER_OF_FILTERED_PARTS)
        ] = filtered_count_by_sound[sound]

    for family in family_abbreviations:
        features[get_family_feature(family, NUMBER_OF_PARTS)] = count_by_family[family]
        features[
            get_family_feature(family, NUMBER_OF_FILTERED_PARTS)
        ] = filtered_count_by_family[family]
        score_data[
            get_family_feature(family, NUMBER_OF_FILTERED_PARTS)
        ] = filtered_count_by_family[family]

    features[get_score_feature(NUMBER_OF_FILTERED_PARTS)] = len(abbreviated_parts)
    features[get_score_feature(NUMBER_OF_PARTS)] = len(score.parts)
    score_data[get_score_feature(NUMBER_OF_FILTERED_PARTS)] = len(abbreviated_parts)
    score_data[get_score_feature(NUMBER_OF_PARTS)] = len(score.parts)

    return score_features.update(features)
