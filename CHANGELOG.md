# Changelog

All notable changes to `musif`, newest first.

## v1.3.0
* Bug fixed in scale degree features
* Bug fixed in relative scale degree features
* Bug fixed in melody features (intervals and motion)
* Bug fixed in rhythm features
* Bug fixed in dynamics features
* Bug fixed in harmony features
* Bug fixed in key features
* Bug fixed in density features
* Bug fixed in texture features
* Bug fixed in lyrics features
* Bug fixed in ambitus features
* Bug fixed in core features
* Bug fixed in tempo and time signature features
* Bug fixed in scoring features
* Bug fixed in music21 features
* Bug fixed in windowed extraction
* Bug fixed in the post-processor
* Renamed motion columns and removed redundant interval columns (breaking change)
* Features extracted with previous versions should be extracted again
* Added a test suite and updated the feature documentation

## v1.2.4
* Fix on lyrics module. Implemeted error output file for error registration.

## v1.2.3
* Minifix on lyrics module

## v1.2.2
* Fix incompatible dependencies on ms3 and webcolors

## v1.2.1
* Added some extra documentation
* Added run_extraction.py, example script for extrating features using musif
* Added erros variable on FeaturesExtractor to store files that were not procesed correctly in error_files.csv file
* fix some dependencies problems
* bug fixing on rhythm features

## v1.2
* Remove musif's native support on jSymbolic features. Add notebook to extract them independently
* Improve documentation
* fix bug on previous release

## v1.1.5
* fix minor bug that caused very unnecesary large memory usage

## v1.1.4
* include MUSIF_ID
* bug fix in dynamic features
* include Key Signature feature
* minor bug fixes in the post-processor
* handling of errors for speciic configurations

## v1.1.1 - v1.1.3
* fixed major bug with music21 automatic onversion to MIDI for jSymbolic features
* added exception handling for jSymbolic
* fixed repeats for MIDI conversion for jSymbolic
* fixed initial anacrusis

## v1.1.0
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

## v1.0.1
* `interval` became `melody`
* some features from `rhythm` were moved into `melody`
* improvements to the docs

## v1.0.0
First Release
