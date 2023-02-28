# `musif` CLI tool

`musif` can also be used as a CLI tool.
If you have musif installed in your environment, you can access it using
`python -m musif`.

Alternatively, you can install musif system-wide with `pipx install musif`
(see pipx documentation for instructions: https://pypa.github.io/pipx/)

Here is the help page of the tool. To show it, just use `python -m musif -- -h` (or
`musif -- -h` if you installed it via `pipx`).

```
NAME
    musif - Python tool for extracting features from music score files.

SYNOPSIS
    musif <flags> [PATHS]...

DESCRIPTION
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

POSITIONAL ARGUMENTS
    PATHS
        one or more paths; if provided, the extraction is limited to them; these paths can be absolute or relative to the current directory; all the paths should contain a common parent part; incompatible with `--source_dir`

FLAGS
    -o, --output_path=OUTPUT_PATH
        Type: str
        Default: 'musif_features.csv'
        output file; extension is added or changed to 'csv'
    -s, --source_dir=SOURCE_DIR
        Type: Optional[str]
        Default: None 
        relative path to the directory; searched recursively; incompatible with other files provided
    -n, --njobs=NJOBS
        Type: int
        Default: -1
        number of jobs used, according to joblib: -1 means "all the available virtual cores"; 1 means no parallel processing
    -c, --cache_dir=CACHE_DIR
        Type: str
        Default: 'musif_cache'
        directory where cache files are saved; set to 'None' to disable
    -e, --extension=EXTENSION
        Type: str
        Default: '.xml'
        extension, including the dot, e.g. '.mid', '.krn', '.mxl'; only has effect if `source_dir` is used
    Additional flags are accepted.
        further flags can be used to change musif's configuration (see the docs for possible options)
```
