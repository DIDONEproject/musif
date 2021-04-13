import glob
from os import path
from typing import Dict, List, Tuple, Union

from music21.converter import parse
from music21.stream import Part, Score
from pandas import DataFrame

from musif.config import Configuration
from musif.extract.features import ambitus, custom, density, interval, key, lyrics, metadata, scale, scoring, texture, time
from musif.extract.features.density import get_notes_and_measures
from musif.extract.features.key import get_key_and_mode
from musif.extract.features.scoring import extract_abbreviated_part, extract_sound, to_abbreviation
from musif.musicxml import MUSICXML_FILE_EXTENSION, analysis, expand_part, get_intervals, get_notes_lyrics, get_repetition_elements, split_wind_layers


class FeaturesExtractor:

    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)

    def extract(self, obj, parts_filter: List[str] = None) -> Union[DataFrame, List[DataFrame]]:
        if isinstance(obj, str):
            if path.isdir(obj):
                return self.from_dir(obj, parts_filter)
            else:
                return self.from_file(obj, parts_filter)
        if isinstance(obj, list):
            return self.from_files(obj, parts_filter)
        raise ValueError(
            f"Unexpected argument {obj} should be a directory, a file path or a list of files paths")

    def from_dir(self, musicxml_scores_dir: str, parts_filter: List[str] = None) -> Union[DataFrame, List[DataFrame]]:
        musicxml_files = glob.glob(path.join(musicxml_scores_dir, f'*.{MUSICXML_FILE_EXTENSION}'))
        corpus_df, score_df, parts_df = self._process_corpora(musicxml_files, parts_filter)
        return score_df

    def from_files(self, musicxml_score_files: List[str], parts_filter: List[str] = None) -> Union[DataFrame, List[DataFrame]]:
        parts_df, score_df, corpus_df = self._process_corpora(musicxml_score_files, parts_filter)
        return score_df

    def from_file(self, musicxml_file: str, parts_filter: List[str] = None) -> Union[DataFrame, List[DataFrame]]:
        parts_df, score_df, corpus_df = self._process_corpora([musicxml_file], parts_filter)
        return score_df

    def _process_corpora(self, musicxml_files: List[str], parts_filter: List[str] = None) -> Tuple[DataFrame, DataFrame, DataFrame]:
        corpus_by_dir = self._group_by_dir(musicxml_files)
        all_corpus_features = []
        all_scores_features = []
        all_parts_features = []
        for corpus_dir, files in corpus_by_dir.items():
            scores_data, parts_data, scores_features, parts_features = self._process_corpus(files, parts_filter)
            corpus_features = self._extract_corpus_features(corpus_dir, scores_data, parts_data, scores_features)
            all_corpus_features.append(corpus_features)
            all_scores_features.extend(scores_features)
            all_parts_features.extend(parts_features)
        return DataFrame(all_corpus_features), DataFrame(all_scores_features), DataFrame(all_parts_features)

    def _group_by_dir(self, files: List[str]) -> Dict[str, List[str]]:
        corpus_by_dir = {}
        for file in files:
            corpus_dir = path.dirname(file)
            if corpus_dir not in corpus_by_dir:
                corpus_by_dir[corpus_dir] = []
            corpus_by_dir[corpus_dir].append(file)
        return corpus_by_dir

    def _process_corpus(self, musicxml_files: List[str], parts_filter: List[str] = None) -> Tuple[List[dict], List[dict], List[dict], List[dict]]:
        corpus_scores_data = []
        corpus_parts_data = []
        scores_features = []
        parts_features = []
        for musicxml_file in musicxml_files:
            score_data, parts_data, score_features, score_parts_features = self._process_score(musicxml_file, parts_filter)
            corpus_scores_data.append(score_data)
            corpus_parts_data.extend(parts_data)
            scores_features.append(score_features)
            parts_features.extend(score_parts_features)
        return corpus_scores_data, corpus_parts_data, scores_features, parts_features

    def _process_score(self, musicxml_file: str, parts_filter: List[str] = None) -> Tuple[dict, List[dict], dict, List[dict]]:
        score_data = self._get_score_data(musicxml_file, parts_filter)
        parts_data = [self._get_part_data(score_data, part) for part in score_data["parts"]]
        parts_features = [self._extract_part_features(score_data, part_data) for part_data in parts_data]
        score_features = self._extract_score_features(score_data, parts_data, parts_features)
        return score_data, parts_data, score_features, parts_features

    def _get_score_data(self, musicxml_file: str, parts_filter: List[str] = None) -> dict:
        score = parse(musicxml_file)
        split_wind_layers(score)
        repetition_elements = get_repetition_elements(score)
        score_key, tonality, mode = get_key_and_mode(score)
        ambitus = analysis.discrete.Ambitus()
        parts = self._filter_parts(score, parts_filter)
        if len(parts) == 0:
            self._cfg.read_logger.warning(f"No parts were found for file {musicxml_file} and filter {','.join(parts_filter)}")
        data = {
            "score": score,
            "file": musicxml_file,
            "repetition_elements": repetition_elements,
            "key": score_key,
            "tonality": tonality,
            "mode": mode,
            "ambitus": ambitus,
            "parts": parts,
        }
        return data

    def _filter_parts(self, score: Score, parts_filter: List[str] = None) -> List[Part]:
        if parts_filter is None:
            return list(score.parts)
        filter = set(parts_filter)
        return [part for part in score.parts if to_abbreviation(part, score.parts, self._cfg) in filter]

    def _get_part_data(self, score_data: dict, part: Part) -> dict:
        expanded_part = expand_part(part, score_data["repetition_elements"])
        notes, sounding_measures, measures = get_notes_and_measures(
            expanded_part)
        lyrics = get_notes_lyrics(notes)
        numeric_intervals, text_intervals = get_intervals(notes)
        ambitus_solution = score_data["ambitus"].getSolution(part)
        ambitus_pitch_span = score_data["ambitus"].getPitchSpan(part)
        sound = extract_sound(part, self._cfg)
        part_abbreviation, sound_abbreviation, part_number = extract_abbreviated_part(sound, part, score_data["parts"], self._cfg)
        family = self._cfg.sound_to_family[sound]
        family_abbreviation = self._cfg.family_to_abbreviation[family]
        family = self._cfg.sound_to_family[sound]
        data = {
            "part": part,
            "part_number": part_number,
            "abbreviation": part_abbreviation,
            "sound": sound,
            "sound_abbreviation": sound_abbreviation,
            "family": family,
            "family_abbreviation": family_abbreviation,
            "expanded_part": expanded_part,
            "notes": notes,
            "lyrics": lyrics,
            "sounding_measures": sounding_measures,
            "measures": measures,
            "numeric_intervals": numeric_intervals,
            "text_intervals": text_intervals,
            "ambitus_solution": ambitus_solution,
            "ambitus_pitch_span": ambitus_pitch_span,
        }
        return data

    def _extract_part_features(self, score_data: dict, part_data: dict) -> dict:
        part_features = {}
        part_features.update(scoring.get_part_features(score_data, part_data, self._cfg, part_features))
        part_features.update(lyrics.get_part_features(score_data, part_data, self._cfg, part_features))
        part_features.update(interval.get_part_features(score_data, part_data, self._cfg, part_features))
        part_features.update(ambitus.get_part_features(score_data, part_data, self._cfg, part_features))
        part_features.update(scale.get_part_features(score_data, part_data, self._cfg, part_features))
        part_features.update(density.get_part_features(score_data, part_data, self._cfg, part_features))
        return part_features

    def _extract_score_features(self, score_data: dict, parts_data: List[dict], parts_features: List[dict]) -> dict:
        score_features = {"FileName": path.basename(score_data["file"])}
        score_features.update(custom.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(metadata.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(key.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(time.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(scoring.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(lyrics.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(interval.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(density.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        score_features.update(texture.get_score_features(score_data, parts_data, self._cfg, parts_features, score_features))
        return score_features

    def _extract_corpus_features(self, corpus_dir: str, scores_data: List[dict], parts_data: List[dict], scores_features: List[dict]) -> dict:
        corpus_features = {"Corpus": corpus_dir}
        corpus_features.update(custom.get_corpus_features(scores_data, parts_data, self._cfg, scores_features, corpus_features))
        corpus_features.update(key.get_corpus_features(scores_data, parts_data, self._cfg, scores_features, corpus_features))
        corpus_features.update(time.get_corpus_features(scores_data, parts_data, self._cfg, scores_features, corpus_features))
        corpus_features.update(scoring.get_corpus_features(scores_data, parts_data, self._cfg, scores_features, corpus_features))
        corpus_features.update(lyrics.get_corpus_features(scores_data, parts_data, self._cfg, scores_features, corpus_features))
        # corpus_features.update(interval.get_corpus_features(scores_data, parts_data, self._cfg, scores_features, corpus_features))
        # corpus_features.update(density.get_corpus_features(scores_data, parts_data, self._cfg, scores_features, corpus_features))
        return corpus_features
