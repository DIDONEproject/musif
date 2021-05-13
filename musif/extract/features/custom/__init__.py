from glob import glob
from os import path
from typing import Generator, List

from musif.config import Configuration
from musif.extract.features import custom


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    features = {}
    for module in get_custom_modules():
        features.update(module.get_score_features(
            score_data, parts_data, cfg, parts_features, score_features))
    return features


def get_corpus_features(scores_data: List[dict], parts_data: List[dict], cfg: Configuration, scores_features: List[dict], corpus_features: dict) -> dict:
    features = {}
    for module in get_custom_modules():
        features.update(module.get_corpus_features(
            scores_data, parts_data, cfg, scores_features, corpus_features))
    return features


def get_custom_modules() -> Generator:
    custom_package_path = custom.__path__[0]
    custom_module_files = [path.basename(file)
                           for file in glob(path.join(custom_package_path, "*"))
                           if not path.basename(file).startswith('__') and path.basename(file).endswith('.py')]
    module_names = ["musif.extract.features.custom." + path.splitext(file)[0]
                    for file in custom_module_files]
    for module_name in module_names:
        yield __import__(module_name, fromlist=[''])
