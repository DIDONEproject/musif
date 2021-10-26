from typing import List

import numpy as np
from pandas import DataFrame

from musif.common.constants import VOICE_FAMILY
from musif.config import Configuration
from musif.extract.common import filter_parts_data, part_matches_filter
from musif.extract.constants import DATA_PARTS_FILTER, DATA_PART_ABBREVIATION
from musif.extract.features.core import DATA_NOTES
from musif.extract.features.prefix import get_part_prefix, get_sound_prefix
from musif.extract.features.scoring import FAMILY_ABBREVIATION, NUMBER_OF_FILTERED_PARTS, PART_ABBREVIATION, \
    SOUND_ABBREVIATION

NOTES = "Notes"
NOTES_MEAN = "NotesMean"
TEXTURE = "Texture"


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    parts_data = filter_parts_data(parts_data, score_data[DATA_PARTS_FILTER])
    if len(parts_data) == 0:
        return
    df_parts = DataFrame(parts_features)
    df_sound = df_parts.groupby(SOUND_ABBREVIATION).aggregate({NOTES: "sum"})
    features={}
    for part_features in parts_features:
        part_prefix = get_part_prefix(part_features[PART_ABBREVIATION])
        features[f"{part_prefix}{NOTES}"] = part_features[NOTES]
        
    for sound_abbreviation in df_sound.index:
        sound_prefix = get_sound_prefix(sound_abbreviation)
        len_notes = df_sound.loc[sound_abbreviation, NOTES].tolist()
        sound_parts = score_features[f"{sound_prefix}{NUMBER_OF_FILTERED_PARTS}"]
        notes_mean = len_notes / sound_parts if sound_parts > 0 else 0
        features[f"{sound_prefix}{NOTES}"] = len_notes
        features[f"{sound_prefix}{NOTES_MEAN}"] = notes_mean
    score_features.update(features)

    df_score = DataFrame(score_features, index=[0])
    # df_score = df_parts.aggregate({NOTES: "sum"})

    notes = {}
    for f in range(0, len(parts_features)):
        if parts_features[f][PART_ABBREVIATION].lower().startswith('vn'):
            # cheap capitalization to preserve I and II in Violins
            notes[parts_features[f][PART_ABBREVIATION][0].upper()+parts_features[f][PART_ABBREVIATION][1:]] = len(parts_data[f][DATA_NOTES])
        elif parts_features[f]['Family'] == VOICE_FAMILY:
            notes[parts_features[f][FAMILY_ABBREVIATION].capitalize()] = int(
                    df_score['Family'+parts_features[f][FAMILY_ABBREVIATION].capitalize()+'_NotesMean'])
        else:
                notes[parts_features[f][SOUND_ABBREVIATION].capitalize()] = int(
                    df_score['Sound'+parts_features[f][SOUND_ABBREVIATION].capitalize()+'_NotesMean'])

    for i, (key, value) in enumerate(notes.items()):
        texture = value / np.asarray(list(notes.values())[i+1:])
        for j, t in enumerate(texture):
            part1 = key
            part2 = list(notes.keys())[j+i+1]
            part1_prefix = get_part_prefix(part1)
            part2_prefix = get_part_prefix(part2)
            score_features[f"{part1_prefix}_{part2_prefix}_{TEXTURE}"] = t


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    if not part_matches_filter(part_data[DATA_PART_ABBREVIATION], score_data[DATA_PARTS_FILTER]):
        return {}
    notes = part_data[DATA_NOTES]
    part_features.update({
        NOTES: len(notes)})
