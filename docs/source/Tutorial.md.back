# Tutorial

Musif is a python library that it born as a tool to develop the Didone Project (https://didone.eu/).

The main aim of this project is to try to find which musical features are meaningful in an emotion recognition task.
To do this, a bast amount of musical features (represented in numerical data) are required to run ML and DL algorithms. MusiF is in charge of that.
it is specialized in a 18 century Operas corpus, but intended to work in other registers as well.

To install, just run 'pip install .' inside musiF folder.

Main object of musiF is The FeatureExtractor(), which read scores in xml format and returns a Dataframe containing all info.
Each row represents a score ( or a window of measures if window mode is activated), and each column a feature.

The extractor will extract the features you require and add metadata information to each score's features.

### Metadata Information
TODO: This now has changed with the new configuration??

???
If you wish to have this metadata included, it has to be placed in form of .csv files in a directory you define in the configuration file (metadata_dir)

These files must have an Id column that will be used to assosiate each metadata file information to each score.
???

### Corpus files

Files no analyze must be saved in a directory in .xml format. 
Module FileName of basic_modules will extract metadata info from file names, so you can adjust filenames/filenamme module to your will so it does you it's more convenient for your corpora.

## Examples

### FeaturesExtractor

'''
from musif.extract.extract import FeaturesExtractor

if __name__ == "__main__":
    path_to_file_or_directory = "FileName.xml" # This can be either a single filename or a folder containing all files

    musescore_dir = "your/musescore/dir"

    extraction = FeaturesExtractor(
        path_to_file / "config_tests.yml", data_dir=path_to_file_or_directory, musescore_dir=musescore_dir).extract()

'''

### Window-based approach

MusiF offers the possibility of extracting sets of features for scores by taking into account only certain windows of measures and then overlapping some measures with the previous window. This extracts the same amount of features than for a single file, but values will correspond to the extraction data of only that window of measures.
The amount of measures to be taken into account for each window, as well as the overlapping quantity is set in the Configuration file. 
It can also be overriden directly when instanciating FeaturesExtractor object.
A window_size equal to None disables window-based approach.

The resulting DataFrame has same amount of columns (features) but **one row per window that is extracted**. Therefore, FeatureExtractor outputs a lis of DataFrames, one corresponding to eachfile (when extracting a whole corpus).

'''
from musif.extract.extract import FeaturesExtractor

def save_windows_dfs(dest, extraction) -> None:
    dest = DEST / 'windows_extraction'
    dest.mkdir(exist_ok=True)
    for index, score in enumerate(extraction):
        score = extraction[index]
        name = score['FileName'][0]
        score.to_csv(dest + name + '_windows.csv')

if __name__ == "__main__":
    extraction = FeaturesExtractor(
        path_to_file / "config_tests.yml", window_size = 8, overlapping = 2).extract()

    if type(extraction) == list:
        save_windows_dfs(DEST, extraction)
    else:
        extraction.to_csv(DEST / 'test.csv', index=False)

'''

## Reports Generator

[TODO: UNDER CONSTRUCTION-. DIDONE SPECIFIC] MusiF is able to generate reports using the data that FeatureExtractor generates. 
It creates excel files for each module and presents them organized according to the metadata information.
The number of factors (num_factors) is the level of digration of the reports. Level 0 will create a single folder containing one file for each module.
Level 1 will create a group of folders, each containing several excel files, grouping scores's data according to each metadata division (Per City, Per Decade, Per Title, and so on).

To generate these reports anit subsequent visualizations, you must use ReportsGenerator musiF's object, eand input the DataFrame that FeaturesExtractor outputs.
'''
from musif.extract.extract import FeaturesExtractor
from musif.reports.generate import ReportsGenerator


if __name__ == "__main__":
    extraction = FeaturesExtractor(
            path_to_file / "config_tests.yml").extract()
            
    ReportsGenerator("scripts/config_tests.yml").generate_reports(extraction, path_to_save_files, num_factors=0, visualizations=True)

'''

## Create your own musiF modules
Visit [custom features](Custom_features.md) tutorial to learn how to implement your own musiF feature calculations :)