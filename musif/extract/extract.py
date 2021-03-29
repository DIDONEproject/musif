import glob
from os import path
from typing import List

import pandas as pd
from music21.converter import parse
from music21.stream import Part, Score
from pandas import DataFrame

from musif.config import Configuration
from musif.extract.features import ambitus, custom, density, interval, key, lyrics, metadata, scale, scoring, time
from musif.extract.features.density import get_notes_and_measures
from musif.extract.features.key import get_key_and_mode
from musif.extract.features.scoring import to_abbreviation
from musif.musicxml import MUSICXML_FILE_EXTENSION, expand_part, get_intervals, get_repetition_elements, split_wind_layers


class FeaturesExtractor:

    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)

    def extract(self, obj, parts_filter: List[str] = None) -> DataFrame:
        if isinstance(obj, str):
            if path.isdir(obj):
                return self.from_dir(obj, parts_filter)
            else:
                return self.from_file(obj, parts_filter)
        if isinstance(obj, list):
            return self.from_files(obj, parts_filter)
        raise ValueError(f"Unexpected argument {obj} should be a directory, a file path or a list of files paths")

    def from_dir(self, musicxml_scores_dir: str, parts_filter: List[str] = None) -> DataFrame:
        musicxml_files = glob.glob(path.join(musicxml_scores_dir, f'*.{MUSICXML_FILE_EXTENSION}'))
        return self.from_files(musicxml_files, parts_filter)

    def from_files(self, musicxml_score_files: List[str], parts_filter: List[str] = None) -> DataFrame:
        score_features = [self.from_file(musicxml_file, parts_filter) for musicxml_file in musicxml_score_files]
        return pd.concat(score_features, axis=0)

    def from_file(self, musicxml_file: str, parts_filter: List[str] = None) -> DataFrame:
        score_data = self._get_score_data(musicxml_file, parts_filter)
        parts_data = [self._get_part_data(score_data, part) for part in score_data["parts"]]

        parts_features = self._extract_part_features(score_data, parts_data)
        # sound_features = self._extract_sound_features(score_data, parts_data)
        # family_features = self._extract_family_features(score_data, parts_data)
        score_features = self._extract_score_features(score_data, parts_data, parts_features)

        return DataFrame([score_features])

    def _get_score_data(self, musicxml_file: str, parts_filter: List[str] = None) -> dict:
        score = parse(musicxml_file)
        split_wind_layers(score)
        repetition_elements = get_repetition_elements(score)
        score_key, tonality, mode = get_key_and_mode(score)
        parts = self._filter_parts(score, parts_filter)
        if len(parts) == 0:
            self._cfg.read_logger.warning(f"No parts were found for file {musicxml_file} and filter {','.join(parts_filter)}")
        return {
            "score": score,
            "file": musicxml_file,
            "repetition_elements": repetition_elements,
            "key": score_key,
            "tonality": tonality,
            "mode": mode,
            "parts": parts,
        }

    def _filter_parts(self, score: Score, parts_filter: List[str] = None) -> List[Part]:
        if parts_filter is None:
            return list(score.parts)
        filter = set(parts_filter)
        return [part for part in score.parts if to_abbreviation(part, score.parts, self._cfg) in filter]

    def _get_part_data(self, score_data: dict, part: Part) -> dict:
        expanded_part = expand_part(part, score_data["repetition_elements"])
        notes, sounding_measures, measures = get_notes_and_measures(expanded_part)
        numeric_intervals, text_intervals = get_intervals(notes)
        data = {
            "part": part,
            "abbreviation": to_abbreviation(part, score_data["parts"], self._cfg),
            "expanded_part": expanded_part,
            "notes": notes,
            "sounding_measures": sounding_measures,
            "measures": measures,
            "numeric_intervals": numeric_intervals,
            "text_intervals": text_intervals,
        }
        return data

    def _extract_part_features(self, score_data: dict, parts_data: List[dict]) -> List[dict]:
        parts_features = []
        for part_data in parts_data:
            part_features = {"FileName": path.basename(score_data["file"])}
            part_features.update(scoring.get_part_features(score_data, part_data, self._cfg, part_features))
            part_features.update(lyrics.get_part_features(score_data, part_data, self._cfg, part_features))
            part_features.update(interval.get_part_features(score_data, part_data, self._cfg, part_features))
            part_features.update(ambitus.get_part_features(score_data, part_data, self._cfg, part_features))
            part_features.update(scale.get_part_features(score_data, part_data, self._cfg, part_features))
            part_features.update(density.get_part_features(score_data, part_data, self._cfg, part_features))
            parts_features.append(part_features)
        return parts_features

    def _extract_score_features(self, score_data: dict, parts_data: List[dict], parts_features: List[dict]) -> dict:
        score_features = {"FileName": path.basename(score_data["file"])}
        score_features.update(scoring.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(key.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(interval.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(time.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(density.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(custom.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(metadata.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        return score_features
