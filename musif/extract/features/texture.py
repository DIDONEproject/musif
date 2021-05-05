from typing import List, Tuple

from pandas import DataFrame

from musif.common.sort import sort_dict
from musif.common.constants import VOICE_FAMILY
from musif.config import Configuration
from musif.extract.features.prefix import get_family_prefix, get_part_prefix, get_score_prefix, get_sound_prefix
from musif.musicxml import Measure, Note, Part
import numpy as np

NOTES = "Notes"
TEXTURE = "Texture"


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:

    if len(parts_data) == 0:
        return {}
    features = {}
    notes = {}
    df_parts = DataFrame(parts_features)

    df_sound = df_parts.groupby("SoundAbbreviation").aggregate(
        {NOTES: "sum"})
    df_score = DataFrame(score_features, index=[0])

    for f in range(0, len(parts_features)):
        if parts_features[f]['PartAbbreviation'].lower().startswith('vn'):
            # cheap capitalization to preserve I and II in Violins
            notes[parts_features[f]['PartAbbreviation'][0].upper()+parts_features[f]['PartAbbreviation'][1:]] = len(parts_data[f]['notes'])
        elif parts_features[f]['Family'] == VOICE_FAMILY:
            notes[parts_features[f]['FamilyAbbreviation'].capitalize()] = int(
                    df_score['Family'+parts_features[f]['FamilyAbbreviation'].capitalize()+'_NotesMean'])
        else:
            if not parts_features[f]['PartAbbreviation'].endswith('II'):
                notes[parts_features[f]['SoundAbbreviation'].capitalize()] = int(
                    df_score['Sound'+parts_features[f]['SoundAbbreviation'].capitalize()+'_NotesMean'])

    for i, (key, value) in enumerate(notes.items()):
        texture = value / np.asarray(list(notes.values())[i+1:])
        for j, t in enumerate(texture):
            part1 = key
            part2 = list(notes.keys())[j+i+1]
            part1_prefix = get_part_prefix(part1)
            part2_prefix = get_part_prefix(part2)
            features[f"{part1_prefix}_{part2_prefix}_{TEXTURE}"] = t

    return features
