from typing import List

from musif.config import ExtractConfiguration
from musif.extract.common import _filter_parts_data
from musif.extract.constants import (DATA_MUSESCORE_SCORE,
                                     DATA_PART_ABBREVIATION)
from musif.extract.features.core.constants import DATA_KEY, DATA_NOTES
from musif.extract.features.prefix import get_part_prefix, get_score_feature

from .constants import *
from .utils import get_emphasised_scale_degrees_relative


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    if score_data[DATA_MUSESCORE_SCORE] is not None:
        notes_per_degree_relative = get_emphasised_scale_degrees_relative(
            part_data[DATA_NOTES], score_data
        )
        if notes_per_degree_relative is None: # No harmonic data in the musescore file (or window)
            return

        all_degrees = sum(value for value in notes_per_degree_relative.values())

        for key, value in notes_per_degree_relative.items():
            part_features[DEGREE_RELATIVE_COUNT.format(key=key)] = value
            part_features[DEGREE_RELATIVE_PER.format(key=key)] = (
                value / all_degrees if all_degrees != 0 else 0
            )


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):

    parts_data = _filter_parts_data(parts_data, cfg.parts_filter)

    features = {}

    if len(parts_data) == 0:
        return

    degree = score_data[DATA_KEY]

    score_notes_per_degree = {}

    for part_data in parts_data:

        notes = part_data[DATA_NOTES]
    if score_data[DATA_MUSESCORE_SCORE] is not None:    
        notes_per_degree_relative = get_emphasised_scale_degrees_relative(
            part_data[DATA_NOTES], score_data
        )
        if notes_per_degree_relative is None:
            # no harmonic data in the musescore file (or window)
            return

        for degree, notes in notes_per_degree_relative.items():
            if degree not in score_notes_per_degree:
                score_notes_per_degree[degree] = 0
            score_notes_per_degree[degree] += notes

    all_score_degrees = sum(value for value in score_notes_per_degree.values())

    for degree, value in score_notes_per_degree.items():
        features[get_score_feature(DEGREE_RELATIVE_COUNT.format(key=degree))] = value
        features[get_score_feature(DEGREE_RELATIVE_PER.format(key=degree))] = (
            value / all_score_degrees if all_score_degrees != 0 else 0
        )

    for part_data, parts_features in zip(parts_data, parts_features):

        part_prefix = get_part_prefix(part_data[DATA_PART_ABBREVIATION])

        for feature in parts_features:
            if "Degree" and "relative" in feature:
                features[f"{part_prefix}{feature}"] = parts_features[feature]

    score_features.update(features)
