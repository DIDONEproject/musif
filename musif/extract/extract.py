import copy
import glob
import inspect
import os
import pickle
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import floor
from os import path
from pathlib import Path, PurePath
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from joblib import Parallel, delayed
from music21.converter import parse
from music21.stream import Measure, Part, Score
from pandas import DataFrame
from tqdm import tqdm

# TODO: I would suggest:
# from musif.extract import constants as C
# because it better allows type checking and autocompletion in editors
import musif.extract.constants as C
from musif.common._constants import BASIC_MODULES, FEATURES_MODULES, GENERAL_FAMILY
from musif.common._utils import get_ariaid
from musif.common.cache import FileCacheIntoRAM, SmartModuleCache
from musif.common.exceptions import MissingFileError, ParseFileError
from musif.common.sort import sort_list
from musif.config import Configuration
from musif.extract.common import _filter_parts_data
from musif.extract.utils import process_musescore_file
from musif.logs import ldebug, lerr, linfo, lwarn, pdebug, perr, pinfo, pwarn
from musif.musicxml import (
    MUSESCORE_FILE_EXTENSION,
    MUSICXML_FILE_EXTENSION,
    split_layers,
)
from musif.musicxml.scoring import (
    ROMAN_NUMERALS_FROM_1_TO_20,
    extract_abbreviated_part,
    extract_sound,
    to_abbreviation,
)

_cache = FileCacheIntoRAM(10000)  # To cache scanned scores


def parse_musicxml_file(
    file_path: str, split_keywords: List[str], expand_repeats: bool = False
) -> Score:
    """
    This function parses a musicxml file and returns a music21 Score object. If
    the file has already been parsed, it will be loaded from cache instead of
    processing it again. Split a part in different parts if the instrument
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
        raise ParseFileError(file_path, str(e))
    return score


def parse_musescore_file(file_path: str, expand_repeats: bool = False) -> pd.DataFrame:
    """
    This function parses a musescore file and returns a pandas dataframe. If the file
    has already been parsed, it will be loaded from cache instead of processing it
    again.
        Parameters
        ----------
        file_path: str
            A path to a music mscx path.
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
        harmonic_analysis = process_musescore_file(file_path, expand_repeats)
        _cache.put(file_path, harmonic_analysis)
    except Exception as e:
        harmonic_analysis = None
        raise ParseFileError(file_path, str(e)) from e
    return harmonic_analysis


# TODO: change name for this function (it looks like it extracts something from musicxml files)


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
    if not (isinstance(obj, list) or isinstance(obj, str) or isinstance(obj, PurePath)):
        raise TypeError(
            f"Unexpected argument {obj} should be a directory, a file path or a list of files paths"
        )
    if isinstance(obj, PurePath):
        obj = str(obj)
    if isinstance(obj, str):
        if path.isdir(obj):
            if check_file:
                files_to_extract = _skip_files(obj, check_file)
                return files_to_extract
            else:
                return sorted(
                    glob.glob(path.join(obj, f"*.{MUSICXML_FILE_EXTENSION}")),
                    key=str.lower,
                )
        elif path.isfile(obj):
            return [obj] if obj.rstrip().endswith(f".{MUSICXML_FILE_EXTENSION}") else []
        else:
            raise ValueError(f"File {obj} doesn't exist")
    return sorted(
        [mxml_file for obj_path in obj for mxml_file in extract_files(obj_path)]
    )


def _skip_files(obj, check_file):
    skipped = []
    files_to_extract = []
    total_files = sorted(
        glob.glob(path.join(obj, f"*.{MUSICXML_FILE_EXTENSION}")), key=str.lower
    )
    parsed_files = pd.read_csv(
        check_file, low_memory=False, sep=",", encoding_errors="replace", header=0
    )["FileName"].tolist()
    for i in total_files:
        if i.replace(obj, "").replace("\\", "").replace("/", "") not in parsed_files:
            files_to_extract.append(i)
        else:
            skipped.append(i.replace(obj, "").replace("\\", ""))
    if skipped:
        pwarn(
            "Some files were skipped because they have been already processed before: "
        )
        print(*skipped, sep=",\n")
        print("Total: ", len(skipped))
    return files_to_extract


def compose_musescore_file_path(
    musicxml_file: str, musescore_dir: Optional[str]
) -> str:
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
        raise ValueError(
            f"The file {musicxml_file} is not a .{MUSICXML_FILE_EXTENSION} file"
        )
    extension_index = musicxml_file.rfind(".")
    musescore_file_path = (
        musicxml_file[:extension_index] + "." + MUSESCORE_FILE_EXTENSION
    )
    if musescore_dir:
        musescore_file_path = path.join(
            musescore_dir, path.basename(musescore_file_path)
        )
    return musescore_file_path


class PartsExtractor:
    """
    Given xml a file or files, extracts the name of the different parts in it.
    Parts will be splitted or not according to what is indicated in the configuration,
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

    def extract(
        self, obj: Union[str, List[str]], check_file: Optional[str] = None
    ) -> List[str]:
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
        musicxml_files = find_xml_files(obj, check_file=check_file)
        parts = list(
            {
                part
                for musicxml_file in musicxml_files
                for part in self._process_score(musicxml_file)
            }
        )
        abbreviated_parts_scoring_order = [
            instr + num
            for instr in self._cfg.scoring_order
            for num in [""] + ROMAN_NUMERALS_FROM_1_TO_20
        ]
        return sort_list(parts, abbreviated_parts_scoring_order)

    def _process_score(self, musicxml_file: str) -> List[str]:
        score = parse_musicxml_file(musicxml_file, self._cfg.split_keywords)
        parts = list(score.parts)
        parts_abbreviations = [self._get_part(part, parts) for part in parts]
        return parts_abbreviations

    def _get_part(self, part: Part, parts: List[Part]) -> str:
        sound = extract_sound(part, self._cfg)
        part_abbreviation, _, _ = extract_abbreviated_part(
            sound, part, parts, self._cfg
        )
        return part_abbreviation


class FilesValidator:
    """
    Checks if each file of a group of files can be parsed with no problems.
    If any file can't be parsed, at the end of the validation list of the file paths will be printed,
    as well as their respective raised error.
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
        musicxml_files = find_xml_files(self._cfg.data_dir)
        if self._cfg.parallel:
            errors = self._validate_in_parallel(musicxml_files)
        else:
            errors = self._validate_sequentially(musicxml_files)
        if len(errors) > 0:
            perr("\n".join(errors), level=self._cfg.console_log_level)
        else:
            pinfo(
                "Finished files validation with 0 errors",
                level=self._cfg.console_log_level,
            )

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
                futures = [
                    executor.submit(self._validate_file, musicxml_file)
                    for musicxml_file in musicxml_files
                ]
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
                musescore_file = compose_musescore_file_path(
                    musicxml_file, self._cfg.musescore_dir
                )
                if not path.isfile(musescore_file):
                    raise MissingFileError(musescore_file)
                parse_musescore_file(musescore_file)
        except (ParseFileError, MissingFileError) as e:
            return str(e)
        return None


class FeaturesExtractor:
    """
    Extract features for a score or a list of scores, according to the parameters established in the configurtaion files.
    It extracts musical features from .xml and .mscx files based on the configuration and stores them in a dictionary (score features)
    that at the end will be returned as a DataFrame.
    Features corresponds to modules placed in musif/features directory, and will be computed in order according to the configuration.
    Some features might depend on the previous ones, so order is important.

    """

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args:  Could be a path to a .yml file, a Configuration object or a dictionary. Length zero or one.
        **kwargs: Get keywords to construct Configuration.
        check_file: .csv file containing a DataFrame for files extrction that already have been parsed, so they will be skipped in the
        extraction process.

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
        self.check_file = kwargs.get("check_file")
        self.regex = re.compile("from {FEATURES_MODULES}.([\w\.]+) import")
        # creates the directory for the cache
        if self._cfg.cache_dir is not None:
            pinfo("Cache activated!")
            Path(self._cfg.cache_dir).mkdir(exist_ok=True)
        # self.logger = MPLogger(self._cfg.log_file, self._cfg.file_log_level)
        # self.logger.start()

    def extract(self) -> DataFrame:
        """
        Extracts features given in the configuration data getting a file, directory or several file paths,
        returning a DataFrame containing musical features.
        Returns
        ------
            Score dataframe with the extracted features of given scores. For one score only, a DataFrem is returned with one row only.
        Raises
        ------
        ParseFileError
           If the musicxml file can't be parsed for any reason.
        KeyError
           If features aren't loaded in corrected order or dependencies
        """
        # TODO: Explain what this function returns if ony one score is requested
        linfo("--- Analyzing scores ---\n".center(120, " "))

        musicxml_files = extract_files(self._cfg.data_dir, check_file=self.check_file)
        if self._cfg.is_requested_musescore_file():
            self._find_mscx_files()
        score_df, parts_df = self._process_corpora(musicxml_files)
        return score_df

    def _process_corpora(
        self, musicxml_files: List[str]
    ) -> Tuple[DataFrame, DataFrame]:
        corpus_by_dir = self._group_by_dir(musicxml_files)
        if self._cfg.window_size:
            for corpus_dir, files in corpus_by_dir.items():
                all_scores_features, all_parts_features = self._process_corpus(files)
                all_dfs = []
                all_parts_dictionaries = []
                for score in all_scores_features:
                    df_score = DataFrame(score)
                    df_score = df_score.reindex(sorted(df_score.columns), axis=1)
                    all_dfs.append(df_score)
                for parts in all_parts_features:
                    df_parts = DataFrame(all_parts_features)
                    df_parts = df_parts.reindex(sorted(df_parts.columns), axis=1)
                    all_parts_dictionaries.append(df_parts)
        else:
            all_scores_features = []
            all_parts_features = []
            for corpus_dir, files in corpus_by_dir.items():
                scores_features, parts_features = self._process_corpus(files)
                all_scores_features.extend(scores_features)
                all_parts_features.extend(parts_features)
            all_dfs = DataFrame(all_scores_features)
            all_dfs = all_dfs.reindex(sorted(all_dfs.columns), axis=1)
            df_parts = DataFrame(all_parts_features)
            df_parts = df_parts.reindex(sorted(df_parts.columns), axis=1)
        return all_dfs, df_parts

    @staticmethod
    def _group_by_dir(files: List[str]) -> Dict[str, List[str]]:
        corpus_by_dir = {}
        for file in files:
            corpus_dir = path.dirname(file)
            if corpus_dir not in corpus_by_dir:
                corpus_by_dir[corpus_dir] = []
            corpus_by_dir[corpus_dir].append(file)
        return corpus_by_dir

    def _process_corpus(
        self, musicxml_files: List[str]
    ) -> Tuple[List[dict], List[dict]]:
        def process_corpus_par(musicxml_file):
            if self._cfg.window_size is not None:
                score_features, score_parts_features = self._process_score_windows(
                    musicxml_file
                )
            else:
                score_features, score_parts_features = self._process_score(
                    musicxml_file
                )
            return score_features, score_parts_features

        result = Parallel(n_jobs=self._cfg.parallel)(
            delayed(process_corpus_par)(fname) for fname in tqdm(musicxml_files)
        )

        # result is now a list of tuples, we need to transpose it:
        scores_features, scores_parts_features = zip(*result)
        # now, let's concatenate the scores_pars_features
        parts_features = [*scores_parts_features]
        return scores_features, parts_features

    def _process_score(self, musicxml_file: str) -> Tuple[dict, List[dict]]:
        pinfo(f"\nProcessing score {musicxml_file}")
        if self._cfg.cache_dir is not None:
            cache_name = Path(self._cfg.cache_dir) / (Path(musicxml_file).stem + ".pkl")
        else:
            cache_name = None
        score_data = self._get_score_data(musicxml_file, load_cache=cache_name)
        parts_data = [
            self._get_part_data(score_data, part)
            for part in score_data[C.DATA_SCORE].parts
        ]
        parts_data = _filter_parts_data(parts_data, self._cfg.parts_filter)
        basic_features, basic_parts_features = self.extract_modules(
            BASIC_MODULES, score_data, parts_data
        )
        score_features, parts_features = self.extract_modules(
            FEATURES_MODULES, score_data, parts_data
        )
        score_features = {**basic_features, **score_features}
        [i.update(parts_features[j]) for j, i in enumerate(basic_parts_features)]
        # __import__('ipdb').set_trace()

        if self._cfg.cache_dir is not None:
            pickle.dump(score_data, open(cache_name, "wb"))
        return score_features, parts_features

    def _process_score_windows(self, musicxml_file: str) -> Tuple[dict, List[dict]]:
        # TODO:
        # the first lines are the same as in _process_score
        # they should be moved in an ad-hoc function
        score_data = self._get_score_data(musicxml_file)
        parts_data = [
            self._get_part_data(score_data, part)
            for part in score_data[C.DATA_SCORE].parts
        ]
        parts_data = _filter_parts_data(parts_data, self._cfg.parts_filter)
        basic_features, basic_parts_features = self.extract_modules(
            BASIC_MODULES, score_data, parts_data
        )
        window_features = {}
        first_window_measure = 0
        last_window_measure = 0
        last_score_measure = (
            score_data["score"].parts[0].getElementsByClass(Measure)[-1].measureNumber
        )
        window_counter = 0
        # TODO: take into accou8nt end of  theme A
        number_windows = (last_score_measure + self._cfg.overlap) // (
            self._cfg.window_size - self._cfg.overlap
        )
        all_windows_features = []
        all_parts_features = []
        while first_window_measure < last_score_measure:
            if (
                int(float(basic_features.get(C.END_OF_THEME_A, "100000")))
                < first_window_measure
            ):
                break
            window_counter += 1
            last_window_measure = first_window_measure + self._cfg.window_size
            pinfo(
                f"\nProcessing window {window_counter} for {musicxml_file} of a total of: {number_windows} windows."
            )
            window_data, window_parts_data = self._select_window_data(
                score_data, parts_data, first_window_measure, last_window_measure
            )
            window_features, parts_window_features = self.extract_modules(
                FEATURES_MODULES, window_data, window_parts_data
            )
            window_features[
                C.WINDOW_RANGE
            ] = f"{first_window_measure} - {last_window_measure}"

            window_features = {**basic_features, **window_features}
            [
                i.update(parts_window_features[j])
                for j, i in enumerate(basic_parts_features)
            ]

            all_windows_features.append(window_features)
            all_parts_features.append(parts_window_features)
            first_window_measure = last_window_measure - self._cfg.overlap
        return all_windows_features, all_parts_features

    def _select_window_data(
        self, score_data: dict, parts_data: dict, first_measure: int, last_measure: int
    ):
        window_data = {}
        window_data = copy.deepcopy(score_data)
        window_parts_data = copy.deepcopy(parts_data)
        transversal_data = {}
        t_s = score_data["parts"][0].getElementsByClass(Measure)[0].timeSignature
        transversal_data[C.GLOBAL_TIME_SIGNATURE] = t_s if t_s else ""
        for i, part in enumerate(window_data["score"].parts):
            read_measures = 0
            elements_to_remove = []
            for measure in part.getElementsByClass(Measure):
                read_measures += 1
                if read_measures <= first_measure or read_measures > last_measure:
                    elements_to_remove.append(measure)
            part.remove(targetOrList=elements_to_remove)
            window_data["parts"][i] = part
            window_parts_data[i]["part"] = part

        if (
            self._cfg.is_requested_musescore_file()
            and score_data[C.DATA_MUSESCORE_SCORE] is not None
        ):
            window_data[C.DATA_MUSESCORE_SCORE] = score_data[
                C.DATA_MUSESCORE_SCORE
            ].loc[
                (score_data[C.DATA_MUSESCORE_SCORE]["mn"] <= last_measure)
                & (score_data[C.DATA_MUSESCORE_SCORE]["mn"] >= first_measure)
            ]
            window_data[C.DATA_MUSESCORE_SCORE].reset_index(
                inplace=True, drop=True, level=0
            )
        window_data = {**transversal_data, **window_data}
        return window_data, window_parts_data

    def extract_modules(self, modules: list, data: dict, parts_data: dict):
        score_features = {}
        parts_features = [{} for _ in range(len(parts_data))]
        for module in self._find_modules(modules):
            self._update_parts_module_features(module, data, parts_data, parts_features)
            self._update_score_module_features(
                module, data, parts_data, parts_features, score_features
            )
        return score_features, parts_features

    def _load_m21_objects(self, musicxml_file: str):
        score = parse_musicxml_file(
            musicxml_file,
            self._cfg.split_keywords,
            expand_repeats=self._cfg.expand_repeats,
        )
        filtered_parts = self._filter_parts(score)
        return score, tuple(filtered_parts)

    def _get_score_data(
        self, musicxml_file: str, load_cache: Optional[Path] = None
    ) -> dict:

        data = None
        if load_cache is not None and load_cache.exists():
            try:
                data = pickle.load(open(load_cache, "rb"))
            except Exception as e:
                perr(
                    f"Error while loading pickled object, continuing with extraction from scratch: {e}"
                )

        if data is None:
            score, filtered_parts = self._load_m21_objects(musicxml_file)
            if len(filtered_parts) == 0:
                lwarn(
                    f"No parts were found for file {musicxml_file} and filter: {','.join(self._cfg.parts_filter)}"
                )
            if self._cfg.is_requested_musescore_file():
                data_musescore = self._get_harmony_data(musicxml_file)
            data = {
                C.DATA_SCORE: score,
                C.DATA_FILE: musicxml_file,
                C.DATA_FILTERED_PARTS: filtered_parts,
                C.DATA_MUSESCORE_SCORE: data_musescore,
            }
            if self._cfg.only_theme_a:
                self._only_theme_a(data)
            if self._cfg.cache_dir is not None:
                m21_objects = SmartModuleCache(
                    (data[C.DATA_SCORE], data[C.DATA_FILTERED_PARTS]),
                    resurrect_reference=(self._load_m21_objects, musicxml_file),
                )
                data[C.DATA_SCORE] = m21_objects[0]
                data[C.DATA_FILTERED_PARTS] = m21_objects[1]
        return data

    def _only_theme_a(self, data):
        score: Score = data[C.DATA_SCORE]

        # extracting theme_a information from metadata
        aria_id = get_ariaid(path.basename(data[C.DATA_FILE]))
        last_measure = 1000000
        for d in self._cfg.scores_metadata[C.THEME_A_METADATA]:
            if d["AriaId"] == aria_id:
                last_measure = floor(float(d.get(C.END_OF_THEME_A, last_measure)))
                break

        # removing everything after end of theme A
        for part in score.parts:
            read_measures = 0
            elements_to_remove = []
            for measure in part.getElementsByClass(Measure):  # type: ignore
                read_measures += 1
                if read_measures > last_measure:
                    elements_to_remove.append(measure)
            part.remove(targetOrList=elements_to_remove)  # type: ignore
        if (
            self._cfg.is_requested_musescore_file()
            and data[C.DATA_MUSESCORE_SCORE] is not None
        ):
            data[C.DATA_MUSESCORE_SCORE] = data[C.DATA_MUSESCORE_SCORE].loc[
                data[C.DATA_MUSESCORE_SCORE]["mn"] <= last_measure
            ]
            data[C.DATA_MUSESCORE_SCORE].reset_index(inplace=True, drop=True)
        return data

    def _get_harmony_data(self, musicxml_file: str) -> pd.DataFrame:
        musescore_file_path = compose_musescore_file_path(
            musicxml_file, self._cfg.musescore_dir
        )
        if musescore_file_path is None:
            lerr(f"Musescore file was not found for {musescore_file_path} file!")
            lerr(f"No harmonic analysis will be extracted.{musescore_file_path}")
        else:
            try:
                data_musescore = parse_musescore_file(
                    musescore_file_path, self._cfg.expand_repeats
                )
            except ParseFileError as e:
                data_musescore = None
                lerr(str(e))
        return data_musescore

    def _filter_parts(self, score: Score) -> List[Part]:
        parts = list(score.parts)
        self._deal_with_dupicated_parts(parts)
        if self._cfg.parts_filter is None:
            return parts
        filter_set = set(self._cfg.parts_filter)
        return (
            part
            for part in parts
            if to_abbreviation(part, parts, self._cfg) in filter_set
        )

    def _deal_with_dupicated_parts(self, parts):
        for part in parts:
            # Keeping onle solo and 1º part of duplicated instruments
            part.id = part.id.replace(" 1º", "")
            part.partAbbreviation = part.partAbbreviation.replace(" 1º", "")
            if "2º" in part.id:
                parts.remove(part)

    def _get_part_data(self, score_data: dict, part: Part) -> dict:
        sound = extract_sound(part, self._cfg)
        part_abbreviation, sound_abbreviation, part_number = extract_abbreviated_part(
            sound, part, score_data[C.DATA_FILTERED_PARTS], self._cfg
        )
        family = self._cfg.sound_to_family.get(sound, GENERAL_FAMILY)
        family_abbreviation = self._cfg.family_to_abbreviation[family]
        data = {
            C.DATA_PART: part,
            C.DATA_PART_NUMBER: part_number,
            C.DATA_PART_ABBREVIATION: part_abbreviation,
            C.DATA_SOUND: sound,
            C.DATA_SOUND_ABBREVIATION: sound_abbreviation,
            C.DATA_FAMILY: family,
            C.DATA_FAMILY_ABBREVIATION: family_abbreviation,
        }
        return data

    def _find_modules(self, modules: str):
        found_features = set()
        to_extract = (
            self._cfg.basic_modules if "basic" in modules else self._cfg.features
        )
        for feature in to_extract:
            module_name = f"{modules}.{feature}.handler"
            module = __import__(module_name, fromlist=[""])
            feature_dependencies = self._extract_feature_dependencies(module)
            for feature_dependency in feature_dependencies:
                if feature_dependency not in found_features:
                    raise ValueError(
                        f"Feature {feature} is dependent on feature {feature_dependency} ({feature_dependency} should appear before {feature} in the configuration)"
                    )
            found_features.add(feature)
            yield module

    def _extract_feature_dependencies(self, module: str) -> List[str]:
        module_code = inspect.getsource(module)
        dependencies = self.regex.findall(module_code)
        dependencies = [
            dependency.split(".")[0]
            for dependency in dependencies
            if dependency.split(".")[0] in self._cfg.features
            and dependency != module.split(".")[-2]
        ]
        return dependencies

    def _update_parts_module_features(
        self,
        module,
        score_data: dict,
        parts_data: List[dict],
        parts_features: List[dict],
    ):
        for part_data, part_features in zip(parts_data, parts_features):
            module_name = (
                str(module.__name__)
                .replace("musif.extract.features.", "")
                .replace(".handler", "")
            )
            ldebug(
                f'Extracting part "{part_data[C.DATA_PART_ABBREVIATION]}" {module_name} features.'
            )
            try:
                module.update_part_objects(
                    score_data, part_data, self._cfg, part_features
                )
            except Exception as e:
                score_name = score_data["file"]
                perr(
                    f"An error occurred while extracting module {module.__name__} in {score_name}!!.\nError: {e}\n"
                )
                raise e
                break

    def _update_score_module_features(
        self,
        module,
        score_data: dict,
        parts_data: List[dict],
        parts_features: List[dict],
        score_features: dict,
    ):
        ldebug(
            f'Extracting score "{score_data[C.DATA_FILE]}" {module.__name__} features.'
        )
        try:
            module.update_score_objects(
                score_data, parts_data, self._cfg, parts_features, score_features
            )
        except Exception as e:
            score_name = score_data["file"]
            perr(
                f"An error occurred while extracting module {module.__name__} in {score_name}!!.\nError: {e}\n"
            )
            raise e

    def _find_mscx_files(self):
        data_dir = self._cfg.data_dir
        if type(data_dir) is list:
            xml_names = data_dir
        else:
            data_dir = Path(data_dir)
            xml_names = data_dir.glob("*.xml")
        for name in xml_names:
            if not os.path.exists(
                compose_musescore_file_path(str(name), self._cfg.musescore_dir)
            ):
                perr(f"\nNo mscx was found for file {name}")
