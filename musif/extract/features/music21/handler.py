from typing import List

from music21.features.base import allFeaturesAsList

from musif.config import ExtractConfiguration
from musif.extract.constants import DATA_SCORE
from .constants import COLUMNS


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    features = allFeaturesAsList(score_data[DATA_SCORE])
    score_features.update(
        {
            COLUMNS[outer] + f"_{i}": f
            for outer in range(len(COLUMNS))
            for i, f in enumerate(features[outer])
        }
    )


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    pass
