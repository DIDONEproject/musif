import glob
import inspect
import os
import pickle
import re
import subprocess
from math import floor
from os import path
from pathlib import Path, PurePath
from subprocess import DEVNULL
from tempfile import mkstemp
from typing import List, Optional, Tuple, Union

import ms3
import pandas as pd
from joblib import Parallel, delayed
from music21.converter import parse
from music21.stream import Measure, Part, Score
from pandas import DataFrame
from tqdm import tqdm

import musif.extract.constants as C
from musif.common._constants import BASIC_MODULES, FEATURES_MODULES, GENERAL_FAMILY
from musif.common._utils import get_ariaid
from musif.cache import CACHE_FILE_EXTENSION, FileCacheIntoRAM, SmartModuleCache, store_score_df
from musif.common.exceptions import FeatureError, ParseFileError
from musif.config import Configuration
from musif.extract.common import _filter_parts_data
from musif.extract.utils import process_musescore_file
from musif.logs import ldebug, lerr, linfo, lwarn, perr, pinfo, pwarn
from musif.musicxml import (
    MUSESCORE_FILE_EXTENSION,
    MUSICXML_FILE_EXTENSION,
    extract_numeric_tempo,
    split_layers,
)
from musif.musicxml.scoring import (
    _extract_abbreviated_part,
    extract_sound,
    to_abbreviation,
)

_cache = FileCacheIntoRAM(10000)  # To cache scanned scores


def parse_filename(
    file_path: str, split_keywords: List[str], expand_repeats: bool = False,
    export_dfs_to: Union[str, PurePath] = None
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
    export_dfs_to: Union[str, PurePath]
     Path to a directory where dataframes containing the score data are exported. If
     None, no score is exported. Default value is None.
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
        if export_dfs_to is not None:
            dest_path = Path(export_dfs_to)
            dest_path /= Path(file_path).with_suffix('.pkl').name
            store_score_df(score, dest_path)
        split_layers(score, split_keywords)
        if expand_repeats:
            score = score.expandRepeats()
        _cache.put(file_path, score)
    except Exception as e:
        print(file_path)
        raise ParseFileError(file_path) from e
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
        print(file_path)
        raise ParseFileError(file_path) from e
    return harmonic_analysis


# TODO: document check_file (or, IMHO, make private) and limit_files
def find_files(
    extension: str,
    obj: Union[str, List[Union[str, PurePath]]],
    limit_files: List[str] = None,
    check_file: str = None,
) -> List[PurePath]:
    """Extracts the paths to files given an extension

    Given a path, a directory path, returns a list of paths to musicxml files found, in
    alphabetic order. If given neither a string nor list of strings raise a TypeError
    and if the file doesn't exists returns a ValueError

    Parameters
    ----------
    extension: str
      A string representing the extension that will be looked for
    obj : Union[str, Iterable[str]]
      A path or directory, or a list of paths or directories

    Returns
    -------
    resp : List[PurePath]
      The list of musicxml files found in the provided arguments
      This list will be returned in alphabetical order

    Raises
    ------
    TypeError
      If the type is not the expected (str or List[str]).

    ValueError
      If the provided string is neither a directory nor a file path
    """
    if obj is None:
        return []
    obj = Path(obj)
    if not obj.exists():
        raise ValueError(f"File {obj} doesn't exist")
    elif obj.is_dir():
        if check_file:
            ret = _skip_files(obj, check_file)
        else:
            ret = sorted(obj.glob(f"*{extension}"))
        if limit_files is not None:
            limit_stems = set(map(lambda x: Path(x).stem, limit_files))
            return [f for f in ret if f.stem in limit_stems]
        else:
            return ret
    elif obj.is_file() and obj.suffix == f"{extension}":
        return [obj]
    else:
        return []


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


class FeaturesExtractor:
    """
    Extract features for a score or a list of scores, according to the parameters
    established in the configurtaion files. It extracts musical features from .xml and
    .mscx files based on the configuration and stores them in a dictionary
    (score features) that at the end will be returned as a DataFrame. Features
    corresponds to modules placed in musif/features directory, and will be computed in
    order according to the configuration. Some features might depend on the previous
    ones, so order is important.

    """

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args:  Could be a path to a .yml file, a Configuration object or a dictionary. Length zero or one.
        **kwargs: Get keywords to construct Configuration.
        check_file: .csv file containing a DataFrame for files extrction that already
            have been parsed, so they will be skipped in the
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
        self.limit_files = kwargs.get("limit_files")
        self.check_file = kwargs.get("check_file")
        self.regex = re.compile("from {FEATURES_MODULES}.([\w\.]+) import")
        # creates the directory for the cache
        if self._cfg.cache_dir is not None:
            pinfo("Cache activated!")
            Path(self._cfg.cache_dir).mkdir(exist_ok=True)

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
        linfo("--- Analyzing scores ---\n".center(120, " "))

        xml_filenames = find_files(
            MUSICXML_FILE_EXTENSION,
            self._cfg.xml_dir,
            limit_files=self.limit_files,
            check_file=self.check_file,
        )
        musescore_filenames = find_files(
            MUSESCORE_FILE_EXTENSION,
            self._cfg.musescore_dir,
            limit_files=self.limit_files,
            check_file=self.check_file,
        )
        if len(musescore_filenames) == 0:
            if self._cfg.is_requested_musescore_file():
                perr(
                    f"\nMusescore files are needed for the following features {C.REQUIRE_MSCORE}, but cannot find musescore files. Those features won't be computed!"
                )
        if len(xml_filenames) > 0:
            filenames = xml_filenames
        elif len(musescore_filenames) > 0:
            filenames = musescore_filenames
        elif self._cfg.cache_dir is not None:
            filenames = find_files(
                CACHE_FILE_EXTENSION,
                self._cfg.cache_dir,
                limit_files=self.limit_files,
                check_file=self.check_file,
            )
        else:
            filenames = []
        if len(filenames) == 0:
            raise FileNotFoundError("No file found for extracting features!")

        score_df = self._process_corpus(filenames)
        return score_df

    def _process_corpus(
        self, filenames: List[PurePath]
    ) -> Tuple[List[dict], List[dict]]:
        def process_corpus_par(filename):
            if self._cfg.window_size is not None:
                score_features = self._process_score_windows(filename)
            else:
                score_features = self._process_score(filename)
            return score_features

        scores_features = Parallel(n_jobs=self._cfg.parallel)(
            delayed(process_corpus_par)(fname) for fname in tqdm(filenames)
        )

        if self._cfg.window_size is not None:
            all_dfs = []
            for score in scores_features:
                df_score = DataFrame(score)
                df_score = df_score.reindex(sorted(df_score.columns), axis=1)
                all_dfs.append(df_score)
            all_dfs = pd.concat(all_dfs, axis=0, keys=range(len(all_dfs)))
        else:
            all_dfs = DataFrame(scores_features)
            all_dfs = all_dfs.reindex(sorted(all_dfs.columns), axis=1)
        return all_dfs

    def _init_score_processing(self, filename: PurePath):
        if self._cfg.cache_dir is not None:
            cache_name = Path(self._cfg.cache_dir) / (
                filename.with_suffix(CACHE_FILE_EXTENSION).name
            )
        else:
            cache_name = None
        score_data = self._get_score_data(filename, load_cache=cache_name)
        parts_data = [
            self._get_part_data(score_data, part)
            for part in score_data[C.DATA_SCORE].parts
        ]
        parts_data = _filter_parts_data(parts_data, self._cfg.parts_filter)
        basic_features = self.extract_modules(BASIC_MODULES, score_data, parts_data)
        return basic_features, cache_name, parts_data, score_data

    def _process_score(self, filename: PurePath) -> Tuple[dict, List[dict]]:

        (
            basic_features,
            cache_name,
            parts_data,
            score_data,
        ) = self._init_score_processing(filename)

        score_features = self.extract_modules(FEATURES_MODULES, score_data, parts_data)
        score_features = {**basic_features, **score_features}
        score_features[C.WINDOW_ID] = 0

        if self._cfg.cache_dir is not None:
            pickle.dump(score_data, open(cache_name, "wb"))
        return score_features

    def _process_score_windows(self, filename: PurePath) -> Tuple[dict, List[dict]]:
        (
            basic_features,
            cache_name,
            parts_data,
            score_data,
        ) = self._init_score_processing(filename)

        score_data[C.GLOBAL_TIME_SIGNATURE] = (
            score_data[C.DATA_FILTERED_PARTS][0]
            .getElementsByClass(Measure)[0]
            .timeSignature
        )

        window_features = {}
        nmeasures = len(score_data[C.DATA_SCORE].parts[0].getElementsByClass(Measure))

        ws = self._cfg.window_size
        hopsize = ws - self._cfg.overlap
        number_windows = (nmeasures - self._cfg.overlap) // hopsize

        all_windows_features = []
        for idx in range(number_windows):
            first_window_measure = idx * hopsize
            last_window_measure = first_window_measure + ws
            window_data, window_parts_data = self._select_window_data(
                score_data, parts_data, first_window_measure, last_window_measure
            )
            window_data.update(
                {k: v for k, v in score_data.items() if k not in window_data}
            )

            window_features = self.extract_modules(
                FEATURES_MODULES, window_data, window_parts_data
            )

            window_features[
                C.WINDOW_RANGE
            ] = f"{first_window_measure} - {last_window_measure}"

            window_features[C.WINDOW_ID] = idx

            window_features = {**basic_features, **window_features}

            all_windows_features.append(window_features)
            first_window_measure = last_window_measure - self._cfg.overlap

        if self._cfg.cache_dir is not None:
            pickle.dump(score_data, open(cache_name, "wb"))
        return all_windows_features

    def _select_window_data(
        self, score_data: dict, parts_data: list, first_measure: int, last_measure: int
    ):
        window_score = score_data[C.DATA_SCORE].measures(
            first_measure, last_measure, indicesNotNumbers=True
        )
        window_parts = window_score.parts
        if (
            self._cfg.is_requested_musescore_file()
            and score_data[C.DATA_MUSESCORE_SCORE] is not None
        ):
            window_mscore = score_data[C.DATA_MUSESCORE_SCORE].loc[
                (score_data[C.DATA_MUSESCORE_SCORE]["mn"] <= last_measure)
                & (score_data[C.DATA_MUSESCORE_SCORE]["mn"] >= first_measure)
            ]
            window_mscore.reset_index(inplace=True, drop=True, level=0)
        window_score_data = {
            C.DATA_SCORE: window_score,
            C.DATA_FILTERED_PARTS: window_parts,
            C.DATA_MUSESCORE_SCORE: window_mscore,
        }

        for i, p in enumerate(window_parts):
            parts_data[i]["part"] = p
        return window_score_data, parts_data

    def extract_modules(self, modules: list, data: dict, parts_data: dict):
        score_features = {}
        parts_features = [{} for _ in range(len(parts_data))]
        for module in self._find_modules(modules):
            self._update_parts_module_features(module, data, parts_data, parts_features)
            self._update_score_module_features(
                module, data, parts_data, parts_features, score_features
            )
        return score_features

    def _load_m21_objects(self, filename: Union[str, PurePath]):
        filename = Path(filename)
        if filename.suffix == MUSESCORE_FILE_EXTENSION:
            # convert to xml in a temporary file
            mscore = self._cfg.mscore_exec
            if mscore is None:
                mscore = ms3.utils.get_musescore("auto")
            if mscore is None:
                raise RuntimeError(
                    "Cannot find musescore executable. Please provide xml files or the path to a musescore installation with the configuration `mscore_exec`"
                )
            if not isinstance(mscore, (list, tuple)):
                # this is needed to allow stuffs like `xvfb-run -a mscore`
                mscore = (mscore,)
            tmp_d, tmp_path = mkstemp(
                prefix=filename.stem, suffix=MUSICXML_FILE_EXTENSION
            )
            process = mscore + ("-fo", tmp_path, filename)
            res = subprocess.run(process, stdout=DEVNULL, stderr=DEVNULL)
            if res.returncode != 0:
                raise RuntimeError(
                    f"Error while converting musescore file to xml: {filename}"
                )
        else:
            tmp_path = filename
        score = parse_filename(
            tmp_path,
            self._cfg.split_keywords,
            expand_repeats=self._cfg.expand_repeats,
            export_dfs_to=self._cfg.dfs_dir
        )
        score.numeric_tempo = extract_numeric_tempo(tmp_path)
        if filename.suffix == MUSESCORE_FILE_EXTENSION:
            os.remove(tmp_path)
        filtered_parts = self._filter_parts(score)
        return score, tuple(filtered_parts)

    def _get_score_data(
        self, filename: PurePath, load_cache: Optional[Path] = None
    ) -> dict:
        pinfo(f"\nProcessing score {filename}")
        data = None
        if load_cache is not None and load_cache.exists():
            try:
                data = pickle.load(open(load_cache, "rb"))
                pinfo(f"File was loaded succesfully from cache.")
            except Exception as e:
                perr(
                    f"Error while loading pickled object, continuing with extraction from scratch: {e}"
                )

        if data is None:
            score, filtered_parts = self._load_m21_objects(filename)
            if len(filtered_parts) == 0:
                lwarn(
                    f"No parts were found for file {filename} and filter: {','.join(self._cfg.parts_filter)}"
                )
            if (
                self._cfg.is_requested_musescore_file()
                and self._cfg.musescore_dir is not None
            ):
                data_musescore = self._get_harmony_data(
                    self._cfg.musescore_dir
                    / filename.with_suffix(MUSESCORE_FILE_EXTENSION).name
                )
            data = {
                C.DATA_SCORE: score,
                C.DATA_FILE: str(filename),
                C.DATA_FILTERED_PARTS: filtered_parts,
                C.DATA_MUSESCORE_SCORE: data_musescore,
            }
            if self._cfg.only_theme_a:
                self._only_theme_a(data)
            if self._cfg.cache_dir is not None:
                m21_objects = SmartModuleCache(
                    (data[C.DATA_SCORE], data[C.DATA_FILTERED_PARTS]),
                    resurrect_reference=(
                        self._load_m21_objects,
                        filename.relative_to("."),
                    ),
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

    def _get_harmony_data(self, filename: PurePath) -> pd.DataFrame:
        if not filename.exists():
            lerr(f"Musescore file was not found for {filename} file!")
            lerr(
                f"These features won't be extracted for {filename}: {C.REQUIRE_MSCORE}"
            )
        else:
            try:
                data_musescore = parse_musescore_file(
                    str(filename), self._cfg.expand_repeats
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
        part_abbreviation, sound_abbreviation, part_number = _extract_abbreviated_part(
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
                raise FeatureError(
                    f"In {score_name} while computing {module.__name__}"
                ) from e

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
            raise FeatureError(
                f"In {score_name} while computing {module.__name__}"
            ) from e
