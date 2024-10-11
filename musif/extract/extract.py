import os
import pickle
import subprocess
import types
from pathlib import Path, PurePath
from subprocess import DEVNULL
from tempfile import mkstemp
from typing import List, Optional, Tuple, Union

import ms3
import pandas as pd
from joblib import Parallel, delayed
from music21.converter import parse, toData
from music21.stream import Measure, Part, Score
from pandas import DataFrame
from tqdm import tqdm
from music21 import stream

import musif.extract.constants as C
from musif.cache import (CACHE_FILE_EXTENSION, FileCacheIntoRAM,
                         SmartModuleCache, store_score_df)
from musif.common._constants import GENERAL_FAMILY
from musif.common.exceptions import FeatureError, ParseFileError
from musif.config import ExtractConfiguration
from musif.extract.common import _filter_parts_data
from musif.extract.utils import (cast_mixed_dtypes,
                                 extract_global_time_signature,
                                 process_musescore_file)
from musif.logs import ldebug, lerr, linfo, lwarn, pdebug, perr, pinfo, pwarn
from musif.musescore import constants as mscore_c
from musif.musicxml import constants as musicxml_c
from musif.musicxml import (extract_numeric_tempo, fix_repeats, name_parts,
                            split_layers)
from musif.musicxml.scoring import (_extract_abbreviated_part, extract_sound,
                                    to_abbreviation)
from music21 import converter
import types

# attach a method to convert it into bytestring
# the first argument of toData is the object to be translated, so that could be the `self` of a class method, perfectly ok
# this must be done before of start the caching, because we are modifying the object!
stream.Stream.toData = toData

def parse_filename(
    file_path: str,
    split_keywords: List[str],
    expand_repeats: bool = False,
    export_dfs_to: Union[str, PurePath] = None,
    remove_unpitched_objects: bool = True,
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
    try:
        score = parse(file_path).makeRests()
        if export_dfs_to is not None:
            dest_path = Path(export_dfs_to)
            dest_path /= Path(file_path).with_suffix(".pkl").name
            store_score_df(score, dest_path)

        # give a name to all parts in the score
        name_parts(score)
        if remove_unpitched_objects:
            unpitched_objs = list(
                score.flatten().getElementsByClass(["PercussionChord", "Unpitched"])
            )
            score.remove(unpitched_objs, recurse=True)
        split_layers(score, split_keywords)
        fix_repeats(score)
        if expand_repeats:
            score = score.expandRepeats()
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
    try:
        harmonic_analysis = process_musescore_file(file_path, expand_repeats)
    except Exception as e:
        harmonic_analysis = None
        print(file_path)
        raise ParseFileError(file_path) from e
    return harmonic_analysis


def find_files(
    extensions: str or List[str],
    base_dir: Union[str, List[Union[str, PurePath]]],
    limit_files: List[str] = None,
    exclude_files: List[str] = None,
) -> List[PurePath]:
    """Extracts the paths to files given an extension

    Given a directory path, return a list of paths of files found, in alphabetic order.
    It searches recursively inside `base_dir`. If `base_dir` is a fileor a list of paths
    or directories with `extension`, it is returned in a list. If given neither a string
    nor list of strings raise a TypeError and if the file doesn't exists returns a
    ValueError.

    Parameters
    ----------
    extension: str or Iterable[str]
        A list of strings representing the extensions that will be looked for
    base_dir : Union[str, Iterable[str]]
        A path or directory
    limit_files: Iterable[str] = None
        List of file names relative to `base_dir`. Only these files are taken.
        Incompatible with `exclude_files`
    exclude_files: Iterable[str] = None
        List of file names relative to `base_dir`. None of these files are taken.
        Incompatible with `limit_files`

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
    if isinstance(extensions, str):
        extensions = [extensions]

    if base_dir is None:
        return []
    base_dir = Path(base_dir)
    if not base_dir.exists():
        raise ValueError(f"File {base_dir} doesn't exist")
    elif base_dir.is_dir():
        ret = []
        for ext in extensions:
            ret += sorted([f for f in base_dir.glob(f"**/*{ext}") if f.is_file()])
        if limit_files is not None:
            limit_stems = set(map(lambda x: Path(x).stem, limit_files))
            return [f for f in ret if f.stem in limit_stems]
        elif exclude_files is not None:
            exclude_stems = set(map(lambda x: Path(x).stem, exclude_files))
            return [f for f in ret if f.stem not in exclude_stems]
        else:
            return ret
    elif base_dir.is_file() and base_dir.suffix in extensions:
        return [base_dir]
    else:
        return []

import warnings
# Suppress all DeprecationWarning messages, particularly for .flat method
warnings.filterwarnings("ignore", category=DeprecationWarning, module='music21')


#  sorted(obj.glob(f"*{extension}"))
class FeaturesExtractor:
    """
    Extract features for a score or a list of scores, according to the parameters
    established in the configuration files. It extracts musical features using music21
    and ms3 library, based on the configuration and stores them in a dictionary
    (score features) that at the end will be returned as a DataFrame by the
    `extract` method.

    During the parsing, unpitched objects, (e.g. objects referred to percussion
    instruments) may be removed (see the option
    `remove_unpitched_objects` in the configuration).

    """

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args:  Could be a path to a .yml file, an AbstractExtractConfiguration object or a dictionary. Length zero or one.
        **kwargs: Get keywords to construct ExtractConfiguration.
        limit_files: List[str] = None
            List of file names relative to `obj`. Only these files are taken.
            Incompatible with `exclude_files`
        exclude_files: List[str] = None
            List of file names relative to `obj`. None of these files are taken.
            Incompatible with `limit_files`

        Raises
        ------
        TypeError
         - If the type is not the expected (str, dict or ExtractConfiguration).
        ValueError
          - If there is too many arguments(args)
        FileNotFoundError
          - If any of the files/directories path inside the expected configuration doesn't exit.
        """

        self._cfg = ExtractConfiguration(*args, **kwargs)
        self.limit_files = kwargs.get("limit_files") or getattr(
            self._cfg, "limit_files", None
        )
        self.exclude_files = kwargs.get("exclude_files") or getattr(
            self._cfg, "exclude_files", None
        )
        if any(i in self._cfg.features for i in ("music21")) and self._cfg.cache_dir:
            pwarn("\nmusic21's features were requested. musif's caching system is not compatible with these, so cache will be disabled. \n")
            self._cfg.cache_dir = None
            
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
            C.MUSIC21_FILE_EXTENSIONS,
            self._cfg.data_dir,
            limit_files=self.limit_files,
            exclude_files=self.exclude_files,
        )
        musescore_filenames = find_files(
            mscore_c.MUSESCORE_FILE_EXTENSION,
            self._cfg.musescore_dir,
            limit_files=self.limit_files,
            exclude_files=self.exclude_files,
        )
        
        if len(musescore_filenames) == 0:
            if self._cfg.is_requested_musescore_file():
                perr(
                    f"\nMusescore files are needed for the following features {C.REQUIRE_MSCORE}, but cannot find musescore files. Those features won't be computed!"
                )
        if len(xml_filenames) > 0:
            filenames = xml_filenames
        elif self._cfg.cache_dir is not None:
            filenames = find_files(
                CACHE_FILE_EXTENSION,
                self._cfg.cache_dir,
                limit_files=self.limit_files,
                exclude_files=self.exclude_files,
            )
        else:
            filenames = []
        if len(filenames) == 0:
            raise FileNotFoundError("No file found for extracting features! Use data_dir (or cache_dir) to point to your files directory.")

        score_df = self._process_corpus(filenames)

        # fix dtypes
        score_df = score_df.convert_dtypes()
        score_df = score_df.apply(cast_mixed_dtypes, axis=0)

        return score_df

    def _check_for_error_file(self):
        # Check for error file
        try:
            df = pd.read_csv(f'{self._cfg.output_dir}/error_files.csv', low_memory=False)
            df['ErrorFiles'] = df['ErrorFiles'].astype(str)
            df['ErrorFiles'] = df['ErrorFiles'].str.rsplit('/', 1).str[-1]
            errored_files = list(df['ErrorFiles'])
            print(errored_files)
            print("CSV loaded successfully.")
        except Exception:
            # Handle the case where the file is empty
            print("There is no error_files.csv, it will be created and loaded error files are included manually in it.")
            import os
            if not os.path.exists(f'{self._cfg.output_dir}'):
                os.makedirs(f'{self._cfg.output_dir}')

    def _process_corpus(
        self, filenames: List[PurePath]
    ) -> Tuple[List[dict], List[dict]]:
        def process_corpus_par(idx, filename):
            error_files = []
            errors = []
            try:
                if self._cfg.window_size is not None:
                    score_features = self._process_score_windows(idx, filename)
                else:
                    score_features = self._process_score(idx, filename)
            except Exception as e:
                self._check_for_error_file()
                print(f"Error found on {filename}. Saving the filename and error print to {str(self._cfg.output_dir)}/error_files.csv for latter tracking")
                error_files.append(filename)
                errors.append(e)
                df = pd.DataFrame({'ErrorFiles': error_files,
                                   'Errors': errors})
                df.to_csv(str(self._cfg.output_dir)+'/error_files.csv', mode='a', index=False)
                if self._cfg.ignore_errors:
                    lerr(
                        f"Error while extracting features for file {filename}, skipping it because `ignore_errors` is True!"
                    )
                    return {}
                else:
                    raise e
            return score_features

        scores_features = Parallel(n_jobs=self._cfg.parallel)(
            delayed(process_corpus_par)(idx, fname)
            for idx, fname in enumerate(tqdm(filenames))
        )

        if self._cfg.window_size is not None:
            all_dfs = []
            for score in scores_features:
                df_score = DataFrame(score)
                df_score = df_score.reindex(sorted(df_score.columns), axis=1)
                df_score.replace("NA", pd.NA, inplace=True)
                all_dfs.append(df_score)
            all_dfs = pd.concat(all_dfs, axis=0, keys=range(len(all_dfs)))
        else:
            all_dfs = DataFrame(scores_features)
            all_dfs = all_dfs.reindex(sorted(all_dfs.columns), axis=1)
            all_dfs = all_dfs.replace("NA", pd.NA)
        return all_dfs

    def _init_score_processing(self, idx: int, filename: PurePath):
        if self._cfg.cache_dir is not None:
            cache_name = (
                Path(self._cfg.cache_dir)
                # / filename.parent
                / (filename.name + CACHE_FILE_EXTENSION)
            )
            cache_name.parent.mkdir(parents=True, exist_ok=True)
        else:
            cache_name = None
        score_data = self._get_score_data(filename, load_cache=cache_name)
        parts_data = [
            self._get_part_data(score_data, part)
            for part in score_data[C.DATA_SCORE].parts
        ]
        parts_data = _filter_parts_data(parts_data, self._cfg.parts_filter)
        basic_features = self.extract_modules(
            self._cfg.basic_modules_addresses, score_data, parts_data, basic=True
        )
        basic_features[C.ID] = idx
        return basic_features, cache_name, parts_data, score_data

    def _process_score(self, idx: int, filename: PurePath) -> dict:
        (
            basic_features,
            cache_name,
            parts_data,
            score_data,
        ) = self._init_score_processing(idx, filename)
        extract_global_time_signature(score_data)
        score_features = self.extract_modules(
            self._cfg.feature_modules_addresses, score_data, parts_data, basic=False
        )
        score_features = {**basic_features, **score_features}
        score_features[C.WINDOW_ID] = 0

        if self._cfg.cache_dir is not None:
            pickle.dump(score_data, open(cache_name, "wb"))
        return score_features

    def _process_score_windows(self, idx: int, filename: PurePath) -> List[dict]:
        (
            basic_features,
            cache_name,
            parts_data,
            score_data,
        ) = self._init_score_processing(idx, filename)

        extract_global_time_signature(score_data)

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
                self._cfg.feature_modules_addresses,
                window_data,
                window_parts_data,
                basic=False,
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
        filtered_partNames = [i.partName for i in score_data["parts"]]
        window_parts = [
            i for i in window_score.parts if i.partName in filtered_partNames
        ]
        if (
            self._cfg.is_requested_musescore_file()
            and score_data[C.DATA_MUSESCORE_SCORE] is not None
        ):
            window_mscore = score_data[C.DATA_MUSESCORE_SCORE].loc[
                (score_data[C.DATA_MUSESCORE_SCORE]["mn"] <= last_measure)
                & (score_data[C.DATA_MUSESCORE_SCORE]["mn"] >= first_measure)
            ]
            window_mscore.reset_index(inplace=True, drop=True, level=0)
        else:
            window_mscore = None
        window_score_data = {
            C.DATA_SCORE: window_score,
            C.DATA_FILTERED_PARTS: window_parts,
            C.DATA_MUSESCORE_SCORE: window_mscore,
            C.DATA_NUMERIC_TEMPO: score_data[C.DATA_NUMERIC_TEMPO],
        }

        for i, p in enumerate(window_parts):
            parts_data[i]["part"] = p
        return window_score_data, parts_data

    def extract_modules(
        self, packages: list, data: dict, parts_data: dict, basic: bool
    ):
        score_features = {}
        parts_features = [{} for _ in range(len(parts_data))]
        for package in packages:
            for module in self._find_modules(package, basic):
                self._update_parts_module_features(
                    module, data, parts_data, parts_features
                )
                self._update_score_module_features(
                    module, data, parts_data, parts_features, score_features
                )
        return score_features

    def _load_score_data(self, filename: Union[str, PurePath]):
        filename = Path(filename)
        # if filename.suffix == mscore_c.MUSESCORE_FILE_EXTENSION:
        #     # convert to xml in a temporary file
        #     mscore = self._cfg.mscore_exec
        #     if mscore is None:
        #         mscore = ms3.utils.get_musescore("auto")
        #     if mscore is None:
        #         raise RuntimeError(
        #             "Cannot find musescore executable. Please provide xml files or the path to a musescore installation with the configuration `mscore_exec`"
        #         )
        #     # if not isinstance(mscore, (list, tuple)):
        #     #     # this is needed to allow stuffs like `xvfb-run -a mscore`
        #     #     mscore = (mscore,)
        #     # tmp_d, tmp_path = mkstemp(
        #     #     prefix=filename.stem, suffix=C.MUSIC21_FILE_EXTENSIONS[0]
        #     # )
        #     # process = mscore + ("-fo", tmp_path, filename)
        #     # res = subprocess.run(process, stdout=DEVNULL, stderr=DEVNULL)
        #     # if res.returncode != 0:
        #     #     raise RuntimeError(
        #     #         f"Error while converting musescore file to xml: {filename}"
        #         )
        # else:
            # tmp_path = filename
        score = parse_filename(
            filename,
            self._cfg.split_keywords,
            expand_repeats=self._cfg.expand_repeats,
            export_dfs_to=self._cfg.dfs_dir,
            remove_unpitched_objects=self._cfg.remove_unpitched_objects,
        )
        numeric_tempo = extract_numeric_tempo(filename)
        # if filename.suffix == mscore_c.MUSESCORE_FILE_EXTENSION:
        #     os.close(tmp_d)
        #     os.remove(tmp_path)
        filtered_parts = self._filter_parts(score)
        return score, tuple(filtered_parts), numeric_tempo

    def _get_score_data(
        self, filename: PurePath, load_cache: Optional[Path] = None
    ) -> dict:

        data = None 
        info_load_str = ""
        
        if load_cache is not None and load_cache.exists():
            s = converter.parse(filename)
            s.toData = types.MethodType(converter.toData, converter)
            cached_object = SmartModuleCache(s)
            try:
                data = pickle.load(open(load_cache, "rb"))
            except Exception as e:
                info_load_str += f" Error while loading pickled object, continuing with extraction from scratch: {e}"
            else:
                info_load_str += " File was loaded from cache."
            # get bytes
            bytes = cached_object.toData('midi')
            # write to file
            with open('output.mid', 'wb') as f:
                f.write(bytes)
            # save cached object
            pickle.dump(cached_object, open(load_cache, 'wb'))
        
        if data is None:
            try:
                score, filtered_parts, numeric_tempo = self._load_score_data(filename)
            except ParseFileError as e:
                perr(f"Error while parsing file {filename}")
                raise e
            else:
                info_load_str += " XML file parsed succesfully!"
            if len(filtered_parts) == 0:
                lwarn(
                    f"No parts were found for file {filename} and filter: {','.join(self._cfg.parts_filter)}"
                )
            if (
                self._cfg.is_requested_musescore_file()
                and self._cfg.musescore_dir is not None
            ):
                filename_ms3 = (
                    Path(self._cfg.musescore_dir)
                    / filename.with_suffix(mscore_c.MUSESCORE_FILE_EXTENSION).name
                )
                try:
                    data_musescore = self._get_harmony_data(filename_ms3)
                except ParseFileError as e:
                    perr(f"Error while parsing file {filename_ms3}")
                    raise e
                else:
                    info_load_str += " MS3 file parsed succesfully!"
            else:
                data_musescore = None
            data = {
                C.DATA_SCORE: score,
                C.DATA_FILE: str(filename),
                C.DATA_FILTERED_PARTS: filtered_parts,
                C.DATA_MUSESCORE_SCORE: data_musescore,
                C.DATA_NUMERIC_TEMPO: numeric_tempo,
            }
            if len(self._cfg.precache_hooks) > 0:
                for hook in self._cfg.precache_hooks:
                    if isinstance(hook, str):
                        hook = __import__(hook, fromlist=[""])
                    hook.execute(self._cfg, data)
            if self._cfg.cache_dir is not None:
                m21_objects = SmartModuleCache(
                    (data[C.DATA_SCORE], data[C.DATA_FILTERED_PARTS]),
                    resurrect_reference=(
                        self._load_score_data,
                        # filename.relative_to("."),
                        filename,
                    ),
                )
                data[C.DATA_SCORE] = m21_objects[0]
                data[C.DATA_FILTERED_PARTS] = m21_objects[1]

        pdebug(f"\nProcessing score {filename}." + info_load_str)
        return data

    def _get_harmony_data(self, filename: PurePath) -> pd.DataFrame:
        if not filename.exists():
            lerr(f"Musescore file was not found for {filename} file!")
            lerr(
                f"These features won't be extracted for {filename}: {C.REQUIRE_MSCORE}"
            )
            return None
        else:
            try:
                data_musescore = parse_musescore_file(
                    str(filename), self._cfg.expand_repeats
                )
                return data_musescore
            except ParseFileError as e:
                data_musescore = None
                lerr(str(e))
                return None

    def _filter_parts(self, score: Score) -> List[Part]:
        parts = list(score.parts)
        # self._deal_with_dupicated_parts(parts)
        if self._cfg.parts_filter is None or len(self._cfg.parts_filter) == 0:
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
        family_abbreviation = self._cfg.family_to_abbreviation.get(family, family)
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

    def _get_module_or_attribute(self, f, name):
        if hasattr(f, name):
            module = getattr(f, name)
        else:
            try:
                module = __import__(f.__name__ + "." + name, fromlist=[""])
            except ModuleNotFoundError as e:
                return e
        return module

    def _find_modules(self, package: str, basic: bool):
        found_features = set()
        if isinstance(package, str):
            package = __import__(package, fromlist=[""])
        if basic:
            to_extract = self._cfg.basic_modules if self._cfg.basic_modules else []
        else:
            to_extract = self._cfg.features if self._cfg.features else []
        for feature in to_extract:
            feature_package = self._get_module_or_attribute(package, feature)
            if isinstance(feature_package, Exception):
                continue
            module = self._get_module_or_attribute(feature_package, "handler")
            if isinstance(module, Exception):
                raise ImportError(
                    f"It seems {feature}.handler cannot be imported."
                ) from module
            feature_dependencies = getattr(feature_package, "musif_dependencies", [])
            for dependency in feature_dependencies:
                if dependency not in found_features and dependency != feature:
                    raise ValueError(
                        f"Feature {feature} is dependent on feature {dependency} ({dependency} should appear before {feature} in the configuration)"
                    )
                    
            found_features.add(feature)
            yield module

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
