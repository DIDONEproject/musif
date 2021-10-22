import glob
import inspect
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from os import path
from typing import Dict, List, Tuple

from music21.converter import ConverterException, parse
from music21.stream import Part, Score
from pandas import DataFrame
from tqdm import tqdm

from musif.common.cache import Cache
from musif.common.constants import GENERAL_FAMILY, FEATURES_MODULE, RESET_SEQ, get_color
from musif.common.sort import sort
from musif.config import Configuration
from musif.extract.constants import DATA_FAMILY, DATA_FAMILY_ABBREVIATION, DATA_FILE, DATA_FILTERED_PARTS, DATA_PART, \
    DATA_PARTS_FILTER, DATA_PART_ABBREVIATION, DATA_PART_NUMBER, DATA_SCORE, DATA_SOUND, DATA_SOUND_ABBREVIATION
from musif.extract.common import filter_parts_data
from musif.musicxml import MUSICXML_FILE_EXTENSION, split_layers
from musif.musicxml.scoring import ROMAN_NUMERALS_FROM_1_TO_20, extract_abbreviated_part, extract_sound, to_abbreviation

_cache = Cache(10000)  # To cache scanned scores


def parse_file(file_path: str, split_keywords) -> Score:
    score = _cache.get(file_path)
    if score is None:
        try:
            score = parse(file_path)
            split_layers(score, split_keywords)
            _cache.put(file_path, score)
        except ConverterException:
            print(get_color('ERROR')+ '\nThat seems to be an invalid path!', RESET_SEQ)
    return score


class FilesExtractor:
    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)

    def extract(self, obj) -> List[str]:
        if not (isinstance(obj, list) or isinstance(obj, str)):
            raise ValueError(f"Unexpected argument {obj} should be a directory, a file path or a list of files paths")
        musicxml_files = []
        if isinstance(obj, list):
            musicxml_files = list(obj)
        if isinstance(obj, str):
            musicxml_files = sorted(glob.glob(path.join(obj, f"*.{MUSICXML_FILE_EXTENSION}")) if path.isdir(obj) else [obj])
        return musicxml_files


class PartsExtractor:
    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)
        self._files_extractor = FilesExtractor(*args, **kwargs)

    def extract(self, obj) -> List[str]:
        musicxml_files = self._files_extractor.extract(obj)
        parts = list({part for musicxml_file in musicxml_files for part in self._process_score(musicxml_file)})
        abbreviated_parts_scoring_order = [instr + num
                                           for instr in self._cfg.scoring_order
                                           for num in [''] + ROMAN_NUMERALS_FROM_1_TO_20]
        return sort(parts, abbreviated_parts_scoring_order)

    def _process_score(self, musicxml_file: str) -> List[str]:
        score = parse_file(musicxml_file, self._cfg.split_keywords)
        parts = list(score.parts)
        parts_abbreviations = [self._get_part(part, parts) for part in parts]
        return parts_abbreviations

    def _get_part(self, part: Part, parts: List[Part]) -> str:
        sound = extract_sound(part, self._cfg)
        part_abbreviation, _, _ = extract_abbreviated_part(sound, part, parts, self._cfg)
        return part_abbreviation


class FilesValidator:
    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)
        self._files_extractor = FilesExtractor(*args, **kwargs)

    def validate(self, obj) -> None:
        musicxml_files = self._files_extractor.extract(obj)
        if self._cfg.parallel:
            self._validate_in_parallel(musicxml_files)
        else:
            self._validate_sequentially(musicxml_files)

    def _validate_sequentially(self, musicxml_files: List[str]):
        for musicxml_file in tqdm(musicxml_files):
            self._validate_file(musicxml_file)

    def _validate_in_parallel(self, musicxml_files: List[str]):
        with tqdm(total=len(musicxml_files)) as pbar:
            with ProcessPoolExecutor(max_workers=self._cfg.max_processes) as executor:
                futures = [executor.submit(self._validate_file, musicxml_file) for musicxml_file in musicxml_files]
                for _ in tqdm(as_completed(futures)):
                    pbar.update(1)

    def _validate_file(self, musicxml_file: str):
        print(f"Validating file: {musicxml_file}")
        parse_file(musicxml_file, self._cfg.split_keywords)


class FeaturesExtractor:
    def __init__(self, *args, **kwargs):
        self._cfg = Configuration(*args, **kwargs)
        self._files_extractor = FilesExtractor(*args, **kwargs)

    def extract(self, obj, parts_filter: List[str] = None) -> DataFrame:
        print(get_color('WARNING')+'\n---Analyzing scores ---\n'+ RESET_SEQ)
        musicxml_files = self._files_extractor.extract(obj)
        score_df, parts_df = self._process_corpora(musicxml_files, parts_filter)
        return score_df

    def _process_corpora(self, musicxml_files: List[str], parts_filter: List[str] = None) -> Tuple[DataFrame, DataFrame]:
        corpus_by_dir = self._group_by_dir(musicxml_files)
        all_scores_features = []
        all_parts_features = []
        for corpus_dir, files in corpus_by_dir.items():
            scores_features, parts_features = self._process_corpus(files, parts_filter)
            all_scores_features.extend(scores_features)
            all_parts_features.extend(parts_features)
        df_scores = DataFrame(all_scores_features)
        df_scores = df_scores.reindex(sorted(df_scores.columns), axis=1)
        df_parts = DataFrame(all_parts_features)
        df_parts = df_parts.reindex(sorted(df_parts.columns), axis=1)
        return df_scores, df_parts

    @staticmethod
    def _group_by_dir(files: List[str]) -> Dict[str, List[str]]:
        corpus_by_dir = {}
        for file in files:
            corpus_dir = path.dirname(file)
            if corpus_dir not in corpus_by_dir:
                corpus_by_dir[corpus_dir] = []
            corpus_by_dir[corpus_dir].append(file)
        return corpus_by_dir

    def _process_corpus(self, musicxml_files: List[str], parts_filter: List[str] = None) -> Tuple[List[dict], List[dict]]:
        if self._cfg.parallel:
            return self._process_corpus_in_parallel(musicxml_files, parts_filter)
        return self._process_corpus_sequentially(musicxml_files, parts_filter)

    def _process_corpus_sequentially(
        self, musicxml_files: List[str], parts_filter: List[str] = None
    ) -> Tuple[List[dict], List[dict]]:
        scores_features = []
        parts_features = []
        for musicxml_file in tqdm(musicxml_files):
            score_features, score_parts_features = self._process_score(musicxml_file, parts_filter)
            scores_features.append(score_features)
            parts_features.extend(score_parts_features)
        return scores_features, parts_features

    def _process_corpus_in_parallel(
        self, musicxml_files: List[str], parts_filter: List[str] = None
    ) -> Tuple[List[dict], List[dict]]:
        scores_features = []
        parts_features = []

        with tqdm(total=len(musicxml_files)) as pbar:
            with ProcessPoolExecutor(max_workers=self._cfg.max_processes) as executor:
                futures = [executor.submit(self._process_score, musicxml_file, parts_filter)
                           for musicxml_file in musicxml_files]
                for future in tqdm(as_completed(futures)):
                    score_features, score_parts_features = future.result()
                    scores_features.append(score_features)
                    parts_features.extend(score_parts_features)
                    pbar.update(1)
        return scores_features, parts_features

    def _process_score(self, musicxml_file: str, parts_filter: List[str] = None) -> Tuple[dict, List[dict]]:
        self._cfg.read_logger.info(f"Processing score {musicxml_file}")
        score_data = self._get_score_data(musicxml_file, parts_filter)
        parts_data = [self._get_part_data(score_data, part) for part in score_data[DATA_SCORE].parts]
        parts_data = filter_parts_data(parts_data, score_data[DATA_PARTS_FILTER])
        score_features = {}
        parts_features = [{} for _ in range(len(parts_data))]
        for module in self._extract_feature_modules():
            self._update_parts_module_features(module, score_data, parts_data, parts_features)
            self._update_score_module_features(module, score_data, parts_data, parts_features, score_features)
        return score_features, parts_features

    def _get_score_data(self, musicxml_file: str, parts_filter: List[str] = None) -> dict:
        score = parse_file(musicxml_file, self._cfg.split_keywords)
        filtered_parts = self._filter_parts(score, parts_filter)
        if len(filtered_parts) == 0:
            self._cfg.read_logger.warning(f"No parts were found for file {musicxml_file} and filter: {','.join(parts_filter)}")
        data = {
            DATA_SCORE: score,
            DATA_FILE: musicxml_file,
            DATA_FILTERED_PARTS: filtered_parts,
            DATA_PARTS_FILTER: parts_filter,
        }
        return data

    def _filter_parts(self, score: Score, parts_filter: List[str] = None) -> List[Part]:
        if parts_filter is None:
            return list(score.parts)
        filter = set(parts_filter)
        parts = list(score.parts)
        return [part for part in parts if to_abbreviation(part, parts, self._cfg) in filter]

    def _get_part_data(self, score_data: dict, part: Part) -> dict:
        sound = extract_sound(part, self._cfg)
        part_abbreviation, sound_abbreviation, part_number = extract_abbreviated_part(sound, part, score_data[DATA_FILTERED_PARTS], self._cfg)
        family = self._cfg.sound_to_family.get(sound, GENERAL_FAMILY)
        family_abbreviation = self._cfg.family_to_abbreviation[family]
        data = {
            DATA_PART: part,
            DATA_PART_NUMBER: part_number,
            DATA_PART_ABBREVIATION: part_abbreviation,
            DATA_SOUND: sound,
            DATA_SOUND_ABBREVIATION: sound_abbreviation,
            DATA_FAMILY: family,
            DATA_FAMILY_ABBREVIATION: family_abbreviation,
        }
        return data

    def _extract_feature_modules(self) -> list:
        found_features = set()
        for feature in self._cfg.features:
            module_name = f"{FEATURES_MODULE}.{feature}"
            module = __import__(module_name, fromlist=[''])
            feature_dependencies = self._extract_feature_dependencies(module)
            for feature_dependency in feature_dependencies:
                if feature_dependency not in found_features:
                    raise ValueError(f"Feature {feature} is dependent on feature {feature_dependency} ({feature_dependency} should appear before {feature} in the configuration)")
            found_features.add(feature)
            yield module

    def _extract_feature_dependencies(self, module) -> List[str]:
        module_code = inspect.getsource(module)
        dependencies = re.findall(rf"from {FEATURES_MODULE}.([\w\.]+) import", module_code)
        dependencies = [dependency for dependency in dependencies if dependency in self._cfg.features]
        return dependencies

    def _update_parts_module_features(self, module, score_data: dict, parts_data: List[dict], parts_features: List[dict]):
        for part_data, part_features in zip(parts_data, parts_features):
            self._cfg.read_logger.debug(f"Extracting part \"{part_data[DATA_PART_ABBREVIATION]}\" {module.__name__} features.")
            module.update_part_objects(score_data, part_data, self._cfg, part_features)

    def _update_score_module_features(self, module, score_data: dict, parts_data: List[dict], parts_features: List[dict], score_features: dict):
        self._cfg.read_logger.debug(f"Extracting score \"{score_data[DATA_FILE]}\" {module.__name__} features.")
        module.update_score_objects(score_data, parts_data, self._cfg, parts_features, score_features)
