import glob
import inspect
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from os import path
from typing import Dict, List, Optional, Tuple, Union
from urllib.request import parse_keqv_list

import ms3
import pandas as pd
from music21.converter import parse
from music21.stream import Part, Score
from musif.common.cache import Cache
from musif.common.constants import FEATURES_MODULE, GENERAL_FAMILY
from musif.common.sort import sort_list
from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.constants import *
from musif.extract.exceptions import MissingFileError, ParseFileError
from musif.extract.utils import process_musescore_file
from musif.logs import ldebug, lerr, linfo, lwarn, pdebug, perr, pinfo, pwarn

from musif.musicxml import (MUSESCORE_FILE_EXTENSION, MUSICXML_FILE_EXTENSION,
                            split_layers)
from musif.musicxml.scoring import (ROMAN_NUMERALS_FROM_1_TO_20,
                                    extract_abbreviated_part, extract_sound,
                                    to_abbreviation)
from pandas import DataFrame
from tqdm import tqdm

from musif.mlogger import MPLogger

_cache = Cache(10000)  # To cache scanned scores

def parse_musicxml_file(file_path: str, split_keywords: List[str], expand_repeats: bool = False) -> Score:
    """
    This function parses a musicxml file and returns a music21 Score object. If the file has already been parsed,
    it will be loaded from cache instead of processing it again. Split a part in different parts if the instrument
    family is in keywords argument and expands repeats if indicated.

       Parameters
       ----------
       file_path: str
        A path to a music xml path.
       split_keywords: List[str]
         A lists of keywords based on music21 instrument sound names to split in different parts.
       expand_repeats: bool
         Determines whether to expand or not the repetitions. Default value is False.

       Returns
       -------
       resp : Score
         The score saved in cache or the new score parsed with the necessary parts split.

       Raises
       ------
         ParseFileError
           If the xml file can't be parsed for any reason.
       """
    score = _cache.get(file_path)
    if score is not None:
        return score
    try:
        score = parse(file_path)
        split_layers(score, split_keywords)
        if expand_repeats:
            score = score.expandRepeats()
        _cache.put(file_path, score)
    except Exception as e:
        raise ParseFileError(file_path, str(e)) from e
    return score

def parse_musescore_file(file_path: str, expand_repeats: bool = False) -> pd.DataFrame:
    """
    This function parses a musescore file and returns a pandas dataframe. If the file has
    already been parsed, it will be loaded from cache instead of processing it again.

        Parameters
        ----------
        file_path: str
            A path to a music xml path.
        expand_repeats: bool
            Determines whether to expand or not the repetitions. Default value is False.

        Returns
        -------
        resp : pd.DataFrame
            The score saved in cache or the new score parsed in the form of a dataframe.
        Raises
        ------
        ParseFileError
            If the musescore file can't be parsed for any reason.
    """
    harmonic_analysis = _cache.get(file_path)
    if harmonic_analysis is not None:
        return harmonic_analysis
    try:
        harmonic_analysis=process_musescore_file(file_path, expand_repeats)
        _cache.put(file_path, harmonic_analysis)
        
    except Exception as e:
        harmonic_analysis = None
        raise ParseFileError(file_path, str(e)) from e
    return harmonic_analysis

def extract_files(obj: Union[str, List[str]], check_file: str = None) -> List[str]:
    """Extracts the paths to musicxml files

        Given a file path, a directory path, a list of files paths or a list of directories paths, returns a list of
        paths to musicxml files found, in alphabetic order. If given neither a string nor list of strings raise a
        TypeError and if the file doesn't exists returns a ValueError

        Parameters
        ----------
        obj : Union[str, List[str]]
          A path or a list of paths

        Returns
        -------
        resp : List[str]
          The list of musicxml files found in the provided arguments
          This list will be returned in alphabetical order

        Raises
        ------
        TypeError
          If the type is not the expected (str or List[str]).

        ValueError
          If the provided string is neither a directory nor a file path
    """
    if not (isinstance(obj, list) or isinstance(obj, str)):
        raise TypeError(f"Unexpected argument {obj} should be a directory, a file path or a list of files paths")
    if isinstance(obj, str):
        if path.isdir(obj):
            if check_file:
                files_to_extract = skip_files(obj, check_file)
                return files_to_extract
            else:
                return sorted(glob.glob(path.join(obj, f"*.{MUSICXML_FILE_EXTENSION}")), key=str.lower)
        elif path.isfile(obj):
            return [obj] if obj.rstrip().endswith(f".{MUSICXML_FILE_EXTENSION}") else []
        else:
            raise ValueError(f"File {obj} doesn't exist")
    return sorted([mxml_file for obj_path in obj for mxml_file in extract_files(obj_path)])

def skip_files(obj, check_file):
    skipped=[]
    files_to_extract=[]
    total_files = sorted(glob.glob(path.join(obj, f"*.{MUSICXML_FILE_EXTENSION}")), key=str.lower)
    parsed_files = pd.read_csv(check_file, low_memory=False, sep=',', encoding_errors='replace',header=0)['FileName'].tolist()
    for i in total_files:
        if i.replace(obj,'').replace('\\', "") not in parsed_files:
            files_to_extract.append(i)
        else:
            skipped.append(i.replace(obj,'').replace('\\', ""))
    if skipped: 
        pwarn('Some files were skipped because they have been already processed before: ')
        print(*skipped, sep = ",\n")
        print('Total: ',len(skipped))
    return files_to_extract

def compose_musescore_file_path(musicxml_file: str, musescore_dir: Optional[str]) -> str:
    """
    Given a musicxml file name, returns the equivalent musescore file name, withint different directory or not.

    Parameters
    ----------
    musicxml_file: str
        Original musicxml file

    musescore_dir: Optional[str]
        Directory path to musescore file.

    Returns
    -------
    resp: str
        Musescore file path

    Raises
    ------
    ValueError
        If the given file is not a musicxml.

    """
    if not musicxml_file.endswith("." + MUSICXML_FILE_EXTENSION):
        raise ValueError(f"The file {musicxml_file} is not a .{MUSICXML_FILE_EXTENSION} file")
    extension_index = musicxml_file.rfind(".")
    musescore_file_path = musicxml_file[:extension_index] + "." + MUSESCORE_FILE_EXTENSION
    if musescore_dir:
        musescore_file_path = path.join(musescore_dir, path.basename(musescore_file_path))
    return musescore_file_path


class PartsExtractor:
    """
    Given xml file or files, extracts the name of the different parts within it. With or without spliting the parts,
    indicated in the configurations.
    """
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args:  Could be a path to a .yml file, a Configuration object or a dictionary. Length zero or one.
        **kwargs: Get keywords to construct Configuration.

        Raises
        ------
        TypeError
             If the type is not the expected (str, dict or Configuration).
        ValueError
             If there is too many arguments(args)
        FileNotFoundError
             If any of the files/directories path inside the expected configuration doesn't exit.
        """
        self._cfg = Configuration(*args, **kwargs)


    def extract(self, obj: Union[str, List[str]], check_file: Optional[str] = None) -> List[str]:
        """
        Given xml file or files, extracts the name of the different parts within it. With or without spliting the parts,
        indicated in the configurations.

        Parameters
        ---------
        obj : Union[str, List[str]]
          A path or a list of paths

        Returns
        -------
        resp : List[str]
          A list of parts names in the given files

        Raises
        ------
        TypeError
          If the type is not the expected (str or List[str]).

        ValueError
          If the provided string is neither a directory nor a file path
        """
        musicxml_files = extract_files(obj, check_file = check_file)
        parts = list({part for musicxml_file in musicxml_files for part in self._process_score(musicxml_file)})
        abbreviated_parts_scoring_order = [instr + num
                                           for instr in self._cfg.scoring_order
                                           for num in [''] + ROMAN_NUMERALS_FROM_1_TO_20]
        return sort_list(parts, abbreviated_parts_scoring_order)

    def _process_score(self, musicxml_file: str) -> List[str]:
        score = parse_musicxml_file(musicxml_file, self._cfg.split_keywords)
        parts = list(score.parts)
        parts_abbreviations = [self._get_part(part, parts) for part in parts]
        return parts_abbreviations

    def _get_part(self, part: Part, parts: List[Part]) -> str:
        sound = extract_sound(part, self._cfg)
        part_abbreviation, _, _ = extract_abbreviated_part(sound, part, parts, self._cfg)
        return part_abbreviation


class FilesValidator:
    """
    Checks if each file can be parsed. If any file can't be parsed, at the end it will print a list of the file paths
    and their respective raised error.
    """
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args:  Could be a path to a .yml file, a Configuration object or a dictionary. Length zero or one.
        **kwargs: Get keywords to construct Configuration.

        Raises
        ------
        TypeError
          If the type is not the expected (str, dict or Configuration).
        ValueError
           If there is too many arguments(args)
        FileNotFoundError
          If any of the files/directories path inside the expected configuration doesn't exit.
        """

        self._cfg = Configuration(*args, **kwargs)
        
    def validate(self) -> None:
        """
        Checks, sequentially or in parallel, if the given files are parseable. If any file has a problem, at the end
        it will print a list of the file paths and their respective raised error.
        """

        pinfo("Starting files validation", level=self._cfg.console_log_level)
        musicxml_files = extract_files(self._cfg.data_dir)
        if self._cfg.parallel:
            errors = self._validate_in_parallel(musicxml_files)
        else:
            errors = self._validate_sequentially(musicxml_files)
        if len(errors) > 0:
            perr("\n".join(errors), level=self._cfg.console_log_level)
        else:
            pinfo("Finished files validation with 0 errors", level=self._cfg.console_log_level)

    def _validate_sequentially(self, musicxml_files: List[str]) -> List[str]:
        errors = []
        for musicxml_file in tqdm(musicxml_files):
            error = self._validate_file(musicxml_file)
            if error is not None:
                errors.append(error)
        return errors

    def _validate_in_parallel(self, musicxml_files: List[str]) -> List[str]:
        errors = []
        with tqdm(total=len(musicxml_files)) as pbar:
            with ProcessPoolExecutor(max_workers=self._cfg.max_processes) as executor:
                futures = [executor.submit(self._validate_file, musicxml_file) for musicxml_file in musicxml_files]
                for future in as_completed(futures):
                    pbar.update(1)
                    error = future.result()
                    if error is not None:
                        errors.append(error)
        return errors

    def _validate_file(self, musicxml_file: str) -> Optional[str]:
        pdebug(f"Validating file '{musicxml_file}'", level=self._cfg.console_log_level)
        try:
            parse_musicxml_file(musicxml_file, self._cfg.split_keywords)
            if self._cfg.is_requested_musescore_file():
                musescore_file = compose_musescore_file_path(musicxml_file, self._cfg.musescore_dir)
                if not path.isfile(musescore_file):
                    raise MissingFileError(musescore_file)
                parse_musescore_file(musescore_file)
        except (ParseFileError, MissingFileError) as e:
            return str(e)
        return None


class FeaturesExtractor:
    """
    Extract features given in the configuration data getting a file, directory or several files paths,
    returning a DataFrame of the score.
    """
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args:  Could be a path to a .yml file, a Configuration object or a dictionary. Length zero or one.
        **kwargs: Get keywords to construct Configuration.

        Raises
        ------
        TypeError
         - If the type is not the expected (str, dict or Configuration).
        ValueError
          - If there is too many arguments(args)
        FileNotFoundError
          - If any of the files/directories path inside the expected configuration doesn't exit.
        """
        self._cfg = Configuration(*args, **kwargs)
        self.check_file = kwargs.get('check_file')
        # self.logger = MPLogger(self._cfg.log_file, self._cfg.file_log_level)
        # self.logger.start()

        
    def extract(self) -> DataFrame:
        """
        Extracts features given in the configuration data getting a file, directory or several files paths,
        returning a DataFrame of the score.

        Returns
        ------
            Score dataframe with the extracted features of given scores.

        Raises
        ------
        ParseFileError
           If the musicxml file can't be parsed for any reason.
        KeyError
           If features aren't loaded in corrected order or dependencies
        """
        linfo('--- Analyzing scores ---')

        musicxml_files = extract_files(self._cfg.data_dir, check_file=self.check_file)
        score_df, parts_df = self._process_corpora(musicxml_files)
        return score_df

    def _process_corpora(self, musicxml_files: List[str]) -> Tuple[DataFrame, DataFrame]:
        corpus_by_dir = self._group_by_dir(musicxml_files)
        all_scores_features = []
        all_parts_features = []
        for corpus_dir, files in corpus_by_dir.items():
            scores_features, parts_features = self._process_corpus(files)
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

    def _process_corpus(self, musicxml_files: List[str]) -> Tuple[List[dict], List[dict]]:
        if self._cfg.parallel:
            return self._process_corpus_in_parallel(musicxml_files)
        return self._process_corpus_sequentially(musicxml_files)

    def _process_corpus_sequentially(self, musicxml_files: List[str]) -> Tuple[List[dict], List[dict]]:
        scores_features = []
        parts_features = []
        for musicxml_file in tqdm(musicxml_files):
            score_features, score_parts_features = self._process_score(musicxml_file)
            scores_features.append(score_features)
            parts_features.extend(score_parts_features)
        return scores_features, parts_features

    def _process_corpus_in_parallel(self, musicxml_files: List[str]) -> Tuple[List[dict], List[dict]]:
        scores_features = []
        parts_features = []

        with tqdm(total=len(musicxml_files)) as pbar:
            with ProcessPoolExecutor(max_workers=self._cfg.max_processes) as executor:
                futures = [executor.submit(self._process_score,  musicxml_file) for musicxml_file in musicxml_files]
                # iterator = executor.map(self._process_score, musicxml_files)
                # futures=list(iterator)  # collect the results in a list
                for future in as_completed(futures):
                    score_features, score_parts_features = future.result()
                    scores_features.append(score_features)
                    parts_features.extend(score_parts_features)
                    pbar.update(1)
        return scores_features, parts_features

    def _process_score(self, musicxml_file: str) -> Tuple[dict, List[dict]]:
        # linfo(f"\nProcessing score {musicxml_file}")  
        pinfo(f"\nProcessing score {musicxml_file}")
        score_data = self._get_score_data(musicxml_file)
        parts_data = [self._get_part_data(score_data, part) for part in score_data[DATA_SCORE].parts]
        parts_data = filter_parts_data(parts_data, self._cfg.parts_filter)
        score_features = {}
        parts_features = [{} for _ in range(len(parts_data))]
        for module in self._extract_feature_modules():
            self._update_parts_module_features(module, score_data, parts_data, parts_features)
            self._update_score_module_features(module, score_data, parts_data, parts_features, score_features)
        return score_features, parts_features

    def _get_score_data(self, musicxml_file: str) -> dict:
        score = parse_musicxml_file(musicxml_file, self._cfg.split_keywords, expand_repeats=self._cfg.expand_repeats)
        filtered_parts = self._filter_parts(score)
        if len(filtered_parts) == 0:
            lwarn(f"No parts were found for file {musicxml_file} and filter: {','.join(self._cfg.parts_filter)}")
        data = {
            DATA_SCORE: score,
            DATA_FILE: musicxml_file,
            DATA_FILTERED_PARTS: filtered_parts,
        }
        if self._cfg.is_requested_musescore_file():
            data.update(self._get_harmony_data(musicxml_file))
        return data

    def _get_harmony_data(self, musicxml_file: str) -> dict:
        data = {}
        musescore_file_path = compose_musescore_file_path(musicxml_file, self._cfg.musescore_dir)
        if musescore_file_path is None:
            lerr(f"Musescore file was not found for {musescore_file_path} file!")
            lerr(f"No harmonic analysis will be extracted.{musescore_file_path}")
        else:
            try:
                data[DATA_MUSESCORE_SCORE] = parse_musescore_file(musescore_file_path, self._cfg.expand_repeats)
            except ParseFileError as e:
                lerr(str(e))
        return data

    def _filter_parts(self, score: Score) -> List[Part]:
        parts = list(score.parts)

        self._deal_with_dupicated_parts(parts)

        if self._cfg.parts_filter is None:
            return parts
        filter_set = set(self._cfg.parts_filter)
        return [part for part in parts if to_abbreviation(part, parts, self._cfg) in filter_set]

    def _deal_with_dupicated_parts(self, parts):
        for part in parts:
            # Keeping onle solo and 1º part of duplicated instruments
            part.id=part.id.replace(' 1º', '')
            part.partAbbreviation=part.partAbbreviation.replace(' 1º', '')
            if '2º' in part.id:
                parts.remove(part)

    def _get_part_data(self, score_data: dict, part: Part) -> dict:
        sound = extract_sound(part, self._cfg)
        part_abbreviation, sound_abbreviation, part_number = extract_abbreviated_part(
            sound, part, score_data[DATA_FILTERED_PARTS], self._cfg
        )
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
            module_name = f"{FEATURES_MODULE}.{feature}.handler"
            module = __import__(module_name, fromlist=[''])
            feature_dependencies = self._extract_feature_dependencies(module)
            for feature_dependency in feature_dependencies:
                if feature_dependency not in found_features:
                    raise ValueError(
                        f"Feature {feature} is dependent on feature {feature_dependency} ({feature_dependency} should appear before {feature} in the configuration)")
            found_features.add(feature)
            yield module

    def _extract_feature_dependencies(self, module) -> List[str]:
        module_code = inspect.getsource(module)
        dependencies = re.findall(rf"from {FEATURES_MODULE}.([\w\.]+) import", module_code)
        dependencies = [dependency for dependency in dependencies if dependency in self._cfg.features]
        return dependencies

    def _update_parts_module_features(self, module, score_data: dict, parts_data: List[dict],
                                      parts_features: List[dict]):
        for part_data, part_features in zip(parts_data, parts_features):
            module_name=str(module.__name__).replace("musif.extract.features.", '').replace('.handler','')
            ldebug(f"Extracting part \"{part_data[DATA_PART_ABBREVIATION]}\" {module_name} features.")
            try:
                module.update_part_objects(score_data, part_data, self._cfg, part_features)
            except Exception as e:
                score_name=score_data['file']
                perr(f'An error ocurred while extracting module {module.__name__} in {score_name}!!.\nError: {e}\n')
                break

    def _update_score_module_features(self, module, score_data: dict, parts_data: List[dict],
                                      parts_features: List[dict], score_features: dict):
        ldebug(f"Extracting score \"{score_data[DATA_FILE]}\" {module.__name__} features.")
        try:
            module.update_score_objects(score_data, parts_data, self._cfg, parts_features, score_features)
        except Exception as e:
            score_name=score_data['file']
            perr(f'An error ocurred while extracting module {module.__name__} in {score_name}!!.\nError: {e}\n')