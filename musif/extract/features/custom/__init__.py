from os import path

from music21.stream import Score

from musif.config import Configuration
from musif.extract.features.custom.file_name import get_file_name_features


def get_global_features(musicxml_file: str, score: Score, cfg: Configuration) -> dict:
    features = {}
    features.update(get_file_name_features(path.basename(musicxml_file)))
    return features
