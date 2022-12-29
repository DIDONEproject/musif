from typing import List

import numpy as np
from pandas import DataFrame

from musif.common._constants import VOICE_FAMILY
from musif.config import ExtractConfiguration
from musif.extract.basic_modules.scoring.constants import FAMILY
from musif.extract.common import _filter_parts_data, _part_matches_filter
from musif.extract.constants import (
    DATA_FAMILY,
    DATA_FAMILY_ABBREVIATION,
    DATA_PART_ABBREVIATION,
    DATA_SOUND_ABBREVIATION,
)
from musif.extract.features.core.constants import NUM_NOTES
from musif.extract.features.core.handler import DATA_NOTES
from musif.extract.features.prefix import get_part_feature, get_part_prefix

from .constants import *


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    parts_data = _filter_parts_data(parts_data, cfg.parts_filter)

    if len(parts_data) == 0:
        return

    features = {}

    for part_data, part_features in zip(parts_data, parts_features):

        part = part_data[DATA_PART_ABBREVIATION]

        features[get_part_feature(part, NUM_NOTES)] = part_features[NUM_NOTES]

    score_features.update(features)

    notes = {}

    for j, part in enumerate(parts_data):

        if part[DATA_PART_ABBREVIATION].startswith("vn"):

            # capitalization to preserve I and II in Violins

            notes[
                part[DATA_PART_ABBREVIATION][0].upper()
                + part[DATA_PART_ABBREVIATION][1:]
            ] = len(part[DATA_NOTES])

        elif part[DATA_FAMILY] == VOICE_FAMILY:

            notes[part[DATA_FAMILY_ABBREVIATION].capitalize()] = int(
                score_features[
                    FAMILY + part[DATA_FAMILY_ABBREVIATION].capitalize() + "_NotesMean"
                ]
            )

        else:

            abbreviation = (
                part[DATA_SOUND_ABBREVIATION][0].upper()
                + part[DATA_SOUND_ABBREVIATION][1:]
            )

            notes[part[DATA_SOUND_ABBREVIATION].capitalize()] = int(
                score_features["Sound" + abbreviation + "_NotesMean"]
            )

    notes = list(notes.items())
    for i in range(len(notes)):

        key_1, value_1 = notes[i]

        for j in range(i + 1, len(notes)):
            key_2, value_2 = notes[j]
            if value_2 == 0:
                if value_1 > 0:
                    texture = np.inf
                else:
                    texture = np.nan
            else:
                texture = value_1 / value_2

            part1_prefix = get_part_prefix(key_1).replace("_", "")

            part2_prefix = get_part_prefix(key_2).replace("_", "")

            score_features[f"{part1_prefix}|{part2_prefix}_{TEXTURE}"] = texture


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):

    if not _part_matches_filter(part_data[DATA_PART_ABBREVIATION], cfg.parts_filter):

        return {}

    notes = part_data[DATA_NOTES]

    part_features.update({DATA_NOTES: len(notes)})
