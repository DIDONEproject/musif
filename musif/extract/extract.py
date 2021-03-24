import glob
from copy import deepcopy
from os import path
from typing import List, Tuple

import pandas as pd
from music21.converter import parse
from music21.stream import Part, Score
from pandas import DataFrame

from musif.common.utils import read_object_from_yaml_file
from musif.config import Configuration
from musif.extract.features import ambitus, custom, density, interval, key, lyrics, metadata, scale, scoring, time
from musif.extract.features.density import get_notes_and_measures
from musif.extract.features.key import get_key
from musif.extract.features.scoring import to_abbreviation
from musif.musicxml import MUSICXML_FILE_EXTENSION, expand_part, get_repetition_elements, split_wind_layers


class FeaturesExtractor:

    def __init__(self, *args, **kwargs):
        config_data = kwargs
        if not kwargs and args:
            if isinstance(args[0], str):
                config_data = read_object_from_yaml_file(args[0])
            elif isinstance(args[0], dict):
                config_data = args[0]
        self._cfg = Configuration(**config_data)

    def extract(self, obj, parts_filter: List[str] = None) -> Tuple[DataFrame, DataFrame]:
        if isinstance(obj, str):
            if path.isdir(obj):
                return self.from_dir(obj, parts_filter)
            else:
                return self.from_file(obj, parts_filter)
        if isinstance(obj, list):
            return self.from_files(obj, parts_filter)
        raise ValueError(f"Unexpected argument {obj} should be a directory, a file path or a list of files paths")

    def from_dir(self, musicxml_scores_dir: str, parts_filter: List[str] = None) -> Tuple[DataFrame, DataFrame]:
        musicxml_files = glob.glob(path.join(musicxml_scores_dir, f'*.{MUSICXML_FILE_EXTENSION}'))
        return self.from_files(musicxml_files, parts_filter)

    def from_files(self, musicxml_score_files: List[str], parts_filter: List[str] = None) -> Tuple[DataFrame, DataFrame]:
        features_pairs = [self.from_file(musicxml_file, parts_filter) for musicxml_file in musicxml_score_files]
        global_features = [features[0] for features in features_pairs]
        parts_features = [features[1] for features in features_pairs]
        return pd.concat(global_features, axis=0), pd.concat(parts_features, axis=0)

    def from_file(self, musicxml_file: str, parts_filter: List[str] = None) -> Tuple[DataFrame, DataFrame]:
        score = self._parse(musicxml_file)
        parts = self._filter_parts(score, parts_filter)
        if len(parts) == 0:
            self._cfg.read_logger.warning(f"No parts were found for file {musicxml_file} and filter {','.join(parts_filter)}")

        parts_features = self._extract_parts_features(musicxml_file, parts, score)
        global_features = self._extract_global_features(musicxml_file, score, parts_features)

        return DataFrame([global_features]), DataFrame(parts_features)

    def _parse(self, musicxml_file: str) -> Score:
        score = parse(musicxml_file)
        split_wind_layers(score)
        return score

    def _filter_parts(self, score: Score, parts_filter: List[str] = None) -> List[Part]:
        if parts_filter is None:
            return list(score.parts)
        filter = set(parts_filter)
        return [part for part in score.parts if to_abbreviation(part, score.parts, self._cfg) in filter]

    def _extract_parts_features(self, musicxml_file: str, parts: List[Part], score: Score) -> List[dict]:
        repetition_elements = get_repetition_elements(score)
        score_key = get_key(score)
        parts_features = [
            self._extract_single_part_features(musicxml_file, part, score, score_key, repetition_elements)
            for part in parts
        ]
        aggregated_features = self._extract_aggregated_part_features(parts_features)
        return aggregated_features

    def _extract_single_part_features(self, musicxml_file: str, part: Part, score: Score, score_key: str, repetition_elements: List[tuple]) -> dict:
        expanded_part = expand_part(part, repetition_elements)
        notes, sounding_measures, measures = get_notes_and_measures(expanded_part)

        features = {"FileName": path.basename(musicxml_file)}
        features.update(scoring.get_single_part_features(part, score.parts, self._cfg))
        features.update(lyrics.get_single_part_features(expanded_part, notes))
        features.update(interval.get_single_part_features(notes))
        features.update(ambitus.get_single_part_features(expanded_part))
        features.update(scale.get_single_part_features(notes, score_key))
        features.update(density.get_single_part_features(notes, sounding_measures, measures))

        return features

    def _extract_aggregated_part_features(self, parts_features: List[dict]) -> List[dict]:
        features = deepcopy(parts_features)
        self._update_features(features, density.get_aggregated_parts_features(parts_features))
        self._update_features(features, scoring.get_aggregated_parts_features(parts_features))
        return features

    def _update_features(self, features_list: List[dict], update_features_list: List[dict]):
        for features, update_features in zip(features_list, update_features_list):
            features.update(update_features)

    def _extract_global_features(self, musicxml_file: str, score: Score, parts_features: List[dict]) -> dict:
        features = {"FileName": path.basename(musicxml_file)}
        features.update(scoring.get_global_features(parts_features, self._cfg))
        features.update(key.get_global_features(score))
        features.update(time.get_global_features(score))
        features.update(scoring.get_global_features(parts_features, self._cfg))
        features.update(density.get_global_features(parts_features, self._cfg))
        features.update(custom.get_global_features(musicxml_file, score, self._cfg))
        features.update(metadata.get_global_features(features, self._cfg))
        return features
