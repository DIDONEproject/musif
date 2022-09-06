from typing import List

import numpy as np
from pandas import DataFrame

from musif.common._constants import VOICE_FAMILY
from musif.config import Configuration
from musif.extract.common import _filter_parts_data, _part_matches_filter
from musif.extract.constants import DATA_PART_ABBREVIATION
from musif.extract.features.core.handler import DATA_NOTES
from musif.extract.features.prefix import get_part_feature, get_part_prefix
from musif.extract.features.scoring.constants import FAMILY_ABBREVIATION, PART_ABBREVIATION, \
    SOUND_ABBREVIATION
from .constants import *
from ..core.constants import NUM_NOTES


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    parts_data = _filter_parts_data(parts_data, cfg.parts_filter)
    if len(parts_data) == 0:
        return
    features = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]
        features[get_part_feature(part, NUM_NOTES)] = part_features[NUM_NOTES]
        
    score_features.update(features)

    df_score = DataFrame(score_features, index=[0])

    notes = {}
    for f in range(0, len(parts_features)):
        if parts_features[f][PART_ABBREVIATION].lower().startswith('vn'):
            # cheap capitalization to preserve I and II in Violins
            notes[parts_features[f][PART_ABBREVIATION][0].upper()+parts_features[f][PART_ABBREVIATION][1:]] = len(parts_data[f][DATA_NOTES])
        elif parts_features[f]['Family'] == VOICE_FAMILY:
            notes[parts_features[f][FAMILY_ABBREVIATION].capitalize()] = int(
                    score_features['Family' + parts_features[f][FAMILY_ABBREVIATION].capitalize()+'_NotesMean'])
        else:
                abbreviation=parts_features[f][SOUND_ABBREVIATION][0].upper()+parts_features[f][SOUND_ABBREVIATION][1:] #cheap capitalization
                notes[parts_features[f][SOUND_ABBREVIATION].capitalize()] = int(
                    score_features['Sound' + abbreviation+'_NotesMean'])

    for i, (key, value) in enumerate(notes.items()):
        texture = value / np.asarray(list(notes.values())[i+1:])
        for j, t in enumerate(texture):
            part1 = key
            part2 = list(notes.keys())[j+i+1]
            # part1_prefix = get_part_prefix(part1)
            # part2_prefix = get_part_prefix(part2)
            # score_features[f"{part1_prefix}|{part2_prefix}_{TEXTURE}"] = t
            score_features[f"{part1}|{part2}_{TEXTURE}"] = t
            


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    if not _part_matches_filter(part_data[DATA_PART_ABBREVIATION], cfg.parts_filter):
        return {}
    notes = part_data[DATA_NOTES]
    part_features.update({
        DATA_NOTES: len(notes)})
