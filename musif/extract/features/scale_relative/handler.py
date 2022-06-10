from typing import List

from musif.config import Configuration
from musif.extract.common import _filter_parts_data
from musif.extract.constants import DATA_MUSESCORE_SCORE, DATA_PART_ABBREVIATION
from musif.extract.features.prefix import get_part_prefix
from musif.extract.features.scale_relative.utils import get_emphasised_scale_degrees_relative
from .constants import *
from ..core.constants import DATA_NOTES


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    if score_data:
        notes_per_degree_relative = get_emphasised_scale_degrees_relative(part_data[DATA_NOTES], score_data)
        all_degrees = sum(value for value in notes_per_degree_relative.values())

        for key, value in notes_per_degree_relative.items():
            part_features[DEGREE_RELATIVE_COUNT.format(key=key)] = value
            part_features[DEGREE_RELATIVE_PER.format(key=key)] = value / all_degrees if all_degrees != 0 else 0


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):
    parts_data = _filter_parts_data(parts_data, cfg.parts_filter)
    
    if len(parts_data) == 0:
        return

    for part_data, parts_features in zip(parts_data, parts_features):
        part_prefix = get_part_prefix(part_data[DATA_PART_ABBREVIATION])
        for feature in parts_features:
            if "Degree" in feature:
                score_features[f"{part_prefix}{feature}"] = parts_features[feature]
    