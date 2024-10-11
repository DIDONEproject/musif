# musif
<center><img src="https://github.com/DIDONEproject/musif/assets/45066115/a7a5f6f4-57db-4fbb-8e98-91a63cf4eec8" width="450" height="450"></center>

Python library for **Music Feature Extraction and Analysis**, developed by the [Didone Project](https://didone.eu/). 

### Documentation
To read the documentation, please see the website at: https://musif.didone.eu
Includes definitions for musif's functions and classes, definitions for all types of features that musif extracts, as well as example code for using musif.

You will find also two tutorials:
- A basic Tutorial, to just start using musif and extracting some features and even running some ML experiments with them.
- An Advanced Tutorial, to extract features of different corpora and create your own hooks and features.

### Installation
To install the latest version of musif, just run:
`pip install musif`
which will download musif and all its necessary dependencies.

(Good practice is to update your package manager: `python3 -m pip install –-upgrade pip`)

## music21 and jSymbolic features
Currently, musif is able to process and integrate basic music21 features.

For jSymbolic features, musif currently does not support the integration of these features, but a tutorial will be provided to manually merge them into musif's dataframe.

#### jSymbolic installation
Java JRE >= 8 must be installed in your OS. Download jSymbolic from https://sourceforge.net/projects/jmir/files/jSymbolic/

*Important*: right now music21 features are NOT guaranteed to be compatible with musif's cache system. Native musif's features work with cache system just fine. 

## Example
Check and run run_extraction_example.py to see a initial script for extracting xml files by using musif.

## Testing and features extraction
Apart from the documentation of musif, where Tutorials and example code can be found, please feel free to clone and check this repository, where musif is used to extract features from different corpuses
https://github.com/DIDONEproject/music_symbolic_features

## References 

1. A. Llorens, F. Simonetta, M. Serrano, and Á. Torrente, “musif: a Python package for symbolic music feature extraction,” in Proceedings of the Sound and Music Computing Conference, Stockholm, Sweden, 2023.
2. F. Simonetta, A. Llorens, M. Serrano, E. García-Portugués, and Á. Torrente, “Optimizing Feature Extraction for Symbolic Music,” in Proceedings of the 24th International Society for Music Information Retrieval Conference, Milan, Nov. 2023.

## Changelog

#### v1.2.4
* Fix on lyrics module. Implemeted error output file for error registration.

#### v1.2.3
* Minifix on lyrics module

#### v1.2.2
* Fix incompatible dependencies on ms3 and webcolors

#### v1.2.1
* Added some extra documentation
* Added run_extraction.py, example script for extrating features using musif
* Added erros variable on FeaturesExtractor to store files that were not procesed correctly in error_files.csv file
* fix some dependencies problems
* bug fixing on rhythm features

#### v1.2
* Remove musif's native support on jSymbolic features. Add notebook to extract them independently
* Improve documentation
* fix bug on previous release

#### v1.1.5
* fix minor bug that caused very unnecesary large memory usage

#### v1.1.4
* include MUSIF_ID
* bug fix in dynamic features
* include Key Signature feature
* minor bug fixes in the post-processor
* handling of errors for speciic configurations

#### v1.1.1 - v1.1.3
* fixed major bug with music21 automatic onversion to MIDI for jSymbolic features
* added exception handling for jSymbolic
* fixed repeats for MIDI conversion for jSymbolic
* fixed initial anacrusis

#### v1.1.0
* bug fixing
* improved musif parsing abilities for non-well formatted files
* added option `ignore_errors` for ignoring errors while parsing large datasets
* better file naming for cache
* automatically removing unpitched objects (e.g. percussion symbols)
* added `max_nan_rows` and `max_nan_columns` for better NaN handling
* `MUSICXML_EXTENSION` became `MUSIC21_EXTENSION`
* multiple windows and step size for the motion features
* added new module for music21's features
* added new module for jSymbolic's features
* CLI tool with sane defaults; CLI is able to handle all MusicXML extensions

#### v1.0.1
* `interval` became `melody`
* some features from `rhythm` were moved into `melody`
* improvements to the docs

#### v1.0.0
First Release
