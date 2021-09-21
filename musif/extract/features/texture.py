from typing import List

import numpy as np
from pandas import DataFrame

from musif.common.constants import VOICE_FAMILY
from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.constants import DATA_PARTS_FILTER
from musif.extract.features.core import DATA_NOTES
from musif.extract.features.prefix import get_part_prefix
from musif.extract.features.scoring import SOUND_ABBREVIATION, PART_ABBREVIATION, FAMILY_ABBREVIATION

NOTES = "Notes"
TEXTURE = "Texture"


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    parts_data = filter_parts_data(parts_data, score_data[DATA_PARTS_FILTER])
    if len(parts_data) == 0:
        return
    notes = {}
    df_parts = DataFrame(parts_features)
    df_sound = df_parts.groupby(SOUND_ABBREVIATION).aggregate({NOTES: "sum"})
    df_score = DataFrame(score_features, index=[0])

    for f in range(0, len(parts_features)):
        if parts_features[f][PART_ABBREVIATION].lower().startswith('vn'):
            # cheap capitalization to preserve I and II in Violins
            notes[parts_features[f][PART_ABBREVIATION][0].upper()+parts_features[f][PART_ABBREVIATION][1:]] = len(parts_data[f][DATA_NOTES])
        elif parts_features[f]['Family'] == VOICE_FAMILY:
            notes[parts_features[f][FAMILY_ABBREVIATION].capitalize()] = int(
                    df_score['Family'+parts_features[f][FAMILY_ABBREVIATION].capitalize()+'_NotesMean'])
        else:
            # if not parts_features[f]['PartAbbreviation'].endswith('II'):
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
    pass
