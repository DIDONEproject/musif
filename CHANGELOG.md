# Changelog

All notable changes to `musif`, newest first.

## v1.3.1
* Pitches are analysed as they sound: the parts of transposing instruments are transposed by the interval their file states
* Bug fixed in the split of a staff shared by two players (dynamics, text and metre changes were lost or misplaced); a staff is split only when its second voice has notes
* Melodic lines redefined: intervals and motion no longer skip the measures written in several voices
* Dynamics: a silence is not a dynamic level, and parts without markings are NaN
* Rates per quarter note added next to the rates per beat (`...Quarters` columns)
* New column `RepriseInstruction` (da capo or dal segno not written out)
* Harmony: applied chords counted apart (`Harmony_Applied_`), proportions by time (`_PerTime`), new groups for the relative, applied chords and augmented sixths
* Motion features pruned, acceleration removed, and `IntervallicTrimDiff` and `IntervallicTrimRatio` removed (breaking change)
* `Score_VoiceReg` is measured from the tonic of the key
* Bug fixed in the syllable count, the dotted rhythm, the tempo heading and its grouping, and the harmonic additions
* A value that cannot be computed is NaN, never 0 (density, texture, degree proportions, run lengths)
* Post-processor: `replace_nans` replaces an empty cell only where 0 is the measured value
* A score whose annotations state no global key is extracted without harmony features instead of being left empty; a score that failed has no `Presence_of_` values
* Part numbering no longer depends on the cache
* Features extracted with previous versions should be extracted again

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
