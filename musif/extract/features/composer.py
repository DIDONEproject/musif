from typing import List

from musif.config import Configuration

COMPOSER = "Composer"


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:

    score = score_data["score"]
    composer = score.metadata.composer
    return {
        COMPOSER: composer
    }

def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:
    return {}
