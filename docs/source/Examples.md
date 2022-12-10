# Examples

## FeaturesExtractor

'''
from musif.extract.extract import FeaturesExtractor

if __name__ == "__main__":
    path_to_file_or_directory = "FileName.xml" # This can be either a single filename or a folder containing all files

    musescore_dir = "your/musescore/dir"

    extraction = FeaturesExtractor(
        path_to_file / "config_tests.yml", data_dir=path_to_file_or_directory, musescore_dir=musescore_dir).extract()

'''


## Window-based approach

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



