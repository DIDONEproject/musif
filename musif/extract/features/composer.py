from typing import List

from musif.config import Configuration

COMPOSER = "Composer"


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    score = score_data["score"]
    composer = score.metadata.composer
    score_features.update({
        COMPOSER: composer
    })


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    pass
