from typing import List, Tuple

from pandas import DataFrame

from musif.common.sort import sort_dict
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
    notes_list = []
    df_parts = DataFrame(parts_features)

    df_sound = df_parts.groupby("SoundAbbreviation").aggregate(
        {NOTES: "sum"})

    for f in range(0, len(parts_features)):

        # notes_list_parts = np.asanyarray([len(i['notes']) for i in parts_data])

        # notes_list_sounds = np.asanyarray(
        #     [df_sound.loc[sound, NOTES].tolist() for sound in df_sound.index])
        if parts_features[f]['PartAbbreviation'].lower().startswith('vn'):
            print('violin')
            notes_list.append(len(parts_data[f]['notes']))
        else:
            # notes_list.append(df_sound.iloc[f][NOTES])
            pass
        # textures = notes_list[f]/notes_list[f+1:]
        # t_names = [get_part_prefix(parts_features[f]['PartAbbreviation'])+'_'+get_part_prefix(
        #     parts_features[j+f+1]['PartAbbreviation'])+TEXTURE for j in range(0, len(textures))]

        # for i, texture in enumerate(textures):
        #     features[f"{t_names[i]}"] = texture

    for f, sound in enumerate(df_sound.index):
        sound_prefix = get_sound_prefix(sound)
        features[f"{sound_prefix}{NOTES}"] = df_sound.loc[sound, NOTES].tolist()

        # textures = notes_list[f]/notes_list[f+1:]
        # t_names = [get_sound_prefix(df_sound.index[f])+'_'+get_sound_prefix(
        # df_sound.index[j+f+1])+TEXTURE for j in range(0, len(textures))]

        # for i, texture in enumerate(textures):
        #     features[f"{t_names[i]}"] = texture
    return features
