from musif.reports.tasks import textures
from typing import List, Tuple

from pandas import DataFrame

from musif.common.sort import sort_dict
from musif.config import Configuration
from musif.extract.features.prefix import get_family_prefix, get_part_prefix, get_score_prefix, get_sound_prefix
from musif.musicxml import Measure, Note, Part
import numpy as np

NOTES = "Notes"
TEXTURE = "Texture"


def get_textures(len_partvoices, names_list, notes_list):
    textures_list = []

    for f in range(0, len_partvoices):
        texture = [round(notes_list[f]/notes_list[i], 3)
                   for i in range(f, len(notes_list)) if f != i]
        textures_list.append(
            [{f'{names_list[f]}/{names_list[i+f+1]}': texture[i]} for i in range(0, len(texture))])

    return textures_list


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:

    features = {}
    notes_list = []
    df_parts = DataFrame(parts_features)

    df_sound = df_parts.groupby("SoundAbbreviation").aggregate(
        {NOTES: "sum"})

    notes_list = np.asanyarray([len(i['notes']) for i in parts_data])
    for f in range(0, len(parts_features)):
        textures = notes_list[f]/notes_list[f+1:]
        t_names = [get_part_prefix(parts_features[f]['PartAbbreviation'])+'_'+get_part_prefix(
            parts_features[j+f+1]['PartAbbreviation'])+TEXTURE for j in range(0, len(textures))]

        for i, texture in enumerate(textures):
            features[f"{t_names[i]}"] = texture

    for sound in df_sound.index:
        sound_prefix = get_sound_prefix(sound)
        features[f"{sound_prefix}{NOTES}"] = df_sound.loc[sound, NOTES].tolist()
        # features[f"{sound_prefix}{SOUNDING_MEASURES}"] = df_sound.loc[sound,
        #   SOUNDING_MEASURES].tolist()
        # features[f"{sound_prefix}{MEASURES}"] = df_sound.loc[sound,
        #  MEASURES].tolist()
        # features[f"{sound_prefix}{SOUNDING_DENSITY}"] = features[f"{sound_prefix}{NOTES}"] /
        # features[f"{sound_prefix}{SOUNDING_MEASURES}"]
        # features[f"{sound_prefix}{DENSITY}"] = features[f"{sound_prefix}{NOTES}"] /
        # features[f"{sound_prefix}{MEASURES}"]

    return features
