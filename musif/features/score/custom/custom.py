from os import path

from music21.stream import Score

from musif.features.score.custom.file_name import get_file_name_features


def get_custom_features(musicxml_file: str, score: Score) -> dict:
    custom_features = {}
    custom_features.update(get_file_name_features(path.basename(musicxml_file)))
    return custom_features
