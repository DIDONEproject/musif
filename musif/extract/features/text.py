from typing import List

import numpy as np
from pandas import DataFrame

from musif.common.constants import VOICE_FAMILY
from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.features.prefix import get_part_prefix

COMPOSER = "Composer"


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:

    score = score_data["score"]
    composer = score.metadata.composer
    return {
        COMPOSER: composer
    }