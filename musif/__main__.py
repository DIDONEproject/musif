import sys
from typing import Optional
from pathlib import Path

import musif.musicxml.constants as musicxml_c
import musif.extract.constants as extract_c

from musif.config import ExtractConfiguration, PostProcessConfiguration
from musif.extract.extract import FeaturesExtractor
from musif.logs import perr, pinfo
from musif.process.processor import DataProcessor

def main(
    *paths,
    output_path: str = "musif_features.csv",
    source_dir: str = None,
    extension: str = ".xml",
    njobs: int = -1,
    cache_dir: str = "musif_cache",
    ignore_errors: bool = True,
    yaml: str = None,
    tweaks: dict = {},
    harmony: Optional[str] = None,
):
    """
    Python tool for extracting features from music score files.

    This tool uses `music21` to load files, so any file format supported by `music21`
    also works, e.g. MIDI, MusicXML, Kern, ABC files. It uses cache, parallel
    processing, and ignore errors by default. See the options to disable them.

    This tool uses a default configuration that should work well in most cases. See
    [paper] for more benchmarks. By default, it extracts all features except the ones
    that require harmonic annotations. You can use `-y/--yaml` and `-c/--config` for
    more tweaks.

    Examples of usage:
        musif dataset/**/*.mid
            -> process all the midi files in `dataset`, searching files recursively in
            all the sub-directories
        musif *.xml --cache_dir=None
            -> process all xml files in this directory without using cache
        musif --source_dir=dataset --extension=.krn
            -> process all kern files in the directory `dataset`, searching files
            recursively in all the sub-drectories
        musif -- -h
            -> shows this help

    Installation:
        If you have musif installed in your environment, you can access this tool using
        `python -m musif`.

        Alternatively, you can install musif system-wide with `pipx install musif`
        (see pipx documentation for instructions: https://pypa.github.io/pipx/)

    Args:
        paths : one or more paths to file; if provided, the extraction is limited to
            them; these paths can be absolute or relative to the current
            directory; all the paths should contain a common parent part;
            incompatible with `--source_dir`
        output_path : output file; extension is added or changed to 'csv'
        extension : extension, including the dot, e.g. '.mid', '.krn', '.mxl'; only
            has effect if `source_dir` is used, otherwise it's
            inferred from the file names; if one of ['.mxl', '.xml',
            '.musicxml'] is passed, all the other used as well; you can
            set it to a list or to a tuple to include multiple
            extensions;
        source_dir : relative path to the directory; searched recursively;
            incompatible with other files provided
        njobs : number of jobs used, according to joblib: -1 means "all the
            available virtual cores"; 1 means no parallel processing
        cache_dir : directory where cache files are saved; set to 'None' to disable
        ignore_errors : True or False; if False, blocks when a file cannot be
            processed, if True, cprints a warning and continue
        yaml : path to a configuration file that will be used for both extraction and
            post-processing; command line options have the precedence on this yaml file
        tweaks : Further flags can be used to change musif's configuration
            (see the docs for possible options); for this, you should
            pass them as a dictionary, e.g. `musif -t
            '{musescore_dir: "mscore_data"}'`
        harmony : extract harmonic features using musescore files from this directory
    """

    if source_dir is not None and len(paths) > 0:
        perr("Please, provide only one option between `source_dir` and file paths")
        sys.exit(1)

    if source_dir is None and len(paths) == 0:
        perr("Please, provide at least one option between `source_dir` and file paths")
        sys.exit(2)

    if source_dir is None:
        # look for the common parent part into `limit_to_files`
        first_file = Path(paths[0])
        source_dir = first_file.parent

        _source_dir = str(source_dir)
        extension = first_file.suffix

        for file in paths[1:]:
            file_ = Path(file)
            if file_.suffix != extension:
                perr(
                    f"Please provide files with only one extension: first file has extension {extension}, but {file_} has extension {file_.suffix}"
                )
            while not file.startswith(_source_dir):
                source_dir = source_dir.parent
                _source_dir = str(source_dir)
        pinfo(f"Detected parent directory: {_source_dir}")
        pinfo(f"Detected extension: {extension}")
    else:
        paths = None
        if extension in [".xml", ".mxl", ".musicxml"]:
            extension = [".xml", ".mxl", ".musicxml"]

    config = ExtractConfiguration(
        yaml,
        data_dir=source_dir,
        cache_dir=cache_dir,
        parallel=njobs,
        musescore_dir=harmony,
        ignore_errors=ignore_errors,
        **tweaks,
    )
    if config.features == ["core"]:
        config.features = [
            "core",
            "ambitus",
            "melody",
            "tempo",
            "density",
            "texture",
            "lyrics",
            "scale",
            "key",
            "dynamics",
            "rhythm",
            "music21",
        ]
    if harmony is not None:
        config.features += ["harmony", "scale_relative"]
    if len(config.basic_modules) == 0:
        config.basic_modules = ["scoring"]
    extract_c.MUSIC21_FILE_EXTENSIONS = extension
    raw_df = FeaturesExtractor(config, limit_files=paths).extract()
    raw_df = FeaturesExtractor(config, limit_files=paths).extract()

    output_path = Path(output_path).with_suffix(".csv")
    # raw_df.to_csv(output_path.with_suffix(".raw.csv"), index=False)

    config = PostProcessConfiguration(yaml, **tweaks)
    if len(config.columns_contain) == 0:
        config.columns_contain = [
            "_Count",
            "_SmallestInterval",
            "_NumberOfFilteredParts",
        ]
    if len(config.replace_nans) == 0:
        config.replace_nans = ["Interval", "Degree", "Harmony"]
    if config.max_nan_rows is None:
        # if the columns without nans would produce a table with columns/row ratio <
        # 0.25, we remove the rows that are outliers of the 0.99 quantile
        raw_df_na = raw_df.isna()
        num_columns_without_na = (~raw_df_na.any(axis=0)).sum()
        if num_columns_without_na / raw_df.shape[0] < 0.1:
            nans = raw_df_na.sum(axis=1)
            config.max_nan_rows = 1 / 0.99 * nans.quantile(0.99) / raw_df.shape[1]
        else:
            config.max_nan_rows = 1.0
    if config.max_nan_columns is None:
        config.max_nan_columns = 0.0
    processed_df = DataProcessor(raw_df, config).process().data
    # replace empty strings with "NA" only in string columns
    string_cols = processed_df.select_dtypes(include=["object", "string"]).columns
    processed_df[string_cols] = processed_df[string_cols].replace("", "-")
    processed_df.to_csv(output_path, index=False)


if __name__ == "__main__":
    import fire

    fire.Fire(main, name="musif")
