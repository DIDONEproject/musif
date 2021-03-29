from os import path
from typing import List

from musif.config import Configuration
from musif.extract.features.custom.file_name import get_file_name_features


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    features = {}
    features.update(get_file_name_features(path.basename(score_data["file"])))
    return features
