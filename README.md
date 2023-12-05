# musif
![musif](https://github.com/DIDONEproject/musif/assets/45066115/a7a5f6f4-57db-4fbb-8e98-91a63cf4eec8)
Python library for **Music Feature Extraction and Analysis**, developed by the [Didone Project](https://didone.eu/). 

### Documentation
Tho read the documentation, please see the website at: https://musif.didone.eu
Includes definitions for musif's functions and classes, definitions for all type sof features that musif extracts, as well as example code for using musif.

You will find also two tutorials:
- A basic Tutorial, to jus tstart using musif and extracting some features and even running some ML experiments with them.
- An Advanced Tutorial, to extract features of different corpora and create your own hooks and features.

### Installation
To install the latest version of musif, just run
`pip install musif`
which will download musif and all its necessary dependencies.

## jSymbolic and music21 features
Currently, musif is able to process and integrate jsymbolic as well as basic music21 features. If jsymbolic features are selected, Java JRE >= 8 must be installed in your OS and the `JAVA_HOME` environment variable is correctly set (Download Java Development Kit: https://www.oracle.com/es/java/technologies/downloads/). `jSymbolic` will be downloaded automatically at the first run. You can force the download of `jSymbolic` and the check of Java installation by running `python -m musif.extract.features.jsymbolic`.

*Important*: right now music21 and jSymbolic features are NOT guaranteed to be compatible with musif's cache system, unlike some music21 stock features. 
 
In case of problems when installing Java or getting it to work as a command, these sites might be helpful:
https://www.theserverside.com/blog/Coffee-Talk-Java-News-Stories-and-Opinions/How-do-I-install-Java-on-Ubuntu
https://www.wikihow.com/Set-Java-Home

## Testing and features extraction
Apart from the documentation of musif, where Tutorials and example code can be found, please feel free to clone and check this repository, where musif is used to extract features from different corpuses
https://github.com/DIDONEproject/music_symbolic_features

## References 

1. A. Llorens, F. Simonetta, M. Serrano, and Á. Torrente, “musif: a Python package for symbolic music feature extraction,” in Proceedings of the Sound and Music Computing Conference, Stockholm, Sweden, 2023.
2. F. Simonetta, A. Llorens, M. Serrano, E. García-Portugués, and Á. Torrente, “Optimizing Feature Extraction for Symbolic Music,” in Proceedings of the 24th International Society for Music Information Retrieval Conference, Milan, Nov. 2023.

## Changelog

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
