# musif

Python library for **Music Feature Extraction and Analysis**, developed by [Didone Project](https://didone.eu/). 

For more info, see the documentation website at: https://musif.didone.eu

### Instalation
To install the latest version of musif, just run
<pip install musif>
which will download musif and all its necessary dependencies.

# Jsymbolic and music21 features
Currently, musif is able to process and integrate jsymbolic as well as basic music21 features. If jsymbolic features are selected, Java JRE >= 8 installed in your OS and JAVA_HOME included in the environment variables. jSymbolic will be downloaded automatically at the first run. You can force the download of jSymbolic and the check of Java installation by running python -m musif.extract.features.jsymbolicMusif will download JSymbolic automatically and these features will be available during the extraction.
Important: right now jSymbolic features are NOT compatible with musif's cache system, unlike the other stock features and music21 ones). 
 
(In case of problems when installing Java or getting it to work as a command, these sites might be helpful:
https://www.theserverside.com/blog/Coffee-Talk-Java-News-Stories-and-Opinions/How-do-I-install-Java-on-Ubuntu
https://www.wikihow.com/Set-Java-Home)

## Changelog

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
