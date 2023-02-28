import sys
from pathlib import Path

import musif.musicxml.constants as musicxml_c
from musif.config import ExtractConfiguration
from musif.extract.extract import FeaturesExtractor
from musif.logs import perr, pinfo
from musif.process.processor import DataProcessor


def main(
    *paths,
    output_path: str = "musif_features.csv",
    source_dir: str = None,
    njobs: int = -1,
    cache_dir: str = "musif_cache",
    extension: str = ".xml",
    **configs,
):
    """
    Python tool for extracting features from music score files.

    This tool uses `music21` to load files, so any file format supported by `music21`
    also works, e.g. MIDI, MusicXML, Kern, ABC files. It uses cache and parallel
    processing by default. See the options to disable them.

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
        paths : one or more paths; if provided, the extraction is limited to
            them; these paths can be absolute or relative to the current
            directory; all the paths should contain a common parent part;
            incompatible with `--source_dir`
        output_path : output file; extension is added or changed to 'csv'
        extension : extension, including the dot, e.g. '.mid', '.krn', '.mxl'; only
            has effect if `source_dir` is used
        source_dir : relative path to the directory; searched recursively;
            incompatible with other files provided
        njobs : number of jobs used, according to joblib: -1 means "all the
            available virtual cores"; 1 means no parallel processing
        cache_dir : directory where cache files are saved; set to 'None' to disable
        configs : further flags can be used to change musif's configuration (see the
            docs for possible options)
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

    config = ExtractConfiguration(
        None,
        xml_dir=source_dir,
        musescore_dir=None,
        cache_dir="musif_cache/",
        basic_modules=["scoring"],
        features=[
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
        ],
        parallel=njobs,
        **configs,
    )
    musicxml_c.MUSICXML_FILE_EXTENSION = extension
    raw_df = FeaturesExtractor(config, limit_files=paths).extract()

    processed_df = DataProcessor(raw_df, None).process().data
    output_path = Path(output_path).with_suffix(".csv")
    processed_df.to_csv(output_path)


if __name__ == "__main__":
    import fire

    fire.Fire(main, name="musif")
