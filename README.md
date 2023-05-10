# musif

Python library for **Music Feature Extraction and Analysis**, developed by [Didone Project](https://didone.eu/). 

For more info, see the documentation website at: https://musif.didone.eu

### Instalation
To install the latest version of musif, just run
<pip install musif>
which will download musif and all its necessary dependencies. 
IMPORTANT: If jsymbolic featers are selected for extraction, JAVA must be installed and JAVA_HOME included in the environment variables. Musif will download Jsymbolic automatically and these features will be available during the extraction.
(In case oof problems when install Java or geting it to work as a command, these sites might be helpful:
https://www.theserverside.com/blog/Coffee-Talk-Java-News-Stories-and-Opinions/How-do-I-install-Java-on-Ubuntu
https://help.sap.com/docs/SAP_BUSINESSOBJECTS_ANALYSIS,_EDITION_FOR_OLAP/c4341f1ce3324d9d9309163567effc1b/eca795926fdb101497906a7cb0e91070.html )
 
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
