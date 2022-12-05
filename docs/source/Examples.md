# Examples

## FeaturesExtractor

'''
from musif.extract.extract import FeaturesExtractor

path_to_file_or_directory = "FileName.xml"
musescore_dir = your/musescore/dir

extrac = FeaturesExtractor(
    path_to_file / "config_tests.yml", data_dir=path_to_file_or_directory, musescore_dir=musescore_dir).extract()

'''

## Window-based approach

if type(extrac) == list:
    save_windows_dfs(DEST, extrac)
else:
    extrac.to_csv(DEST / 'test.csv', index=False)

# ReportsGenerator

ReportsGenerator("scripts/config_tests.yml").generate_reports(extraction, path, num_factors=0, visualizations=True)




def save_windows_dfs(dest, extraction) -> None:
    dest = DEST / 'windows_extraction'
    dest.mkdir(exist_ok=True)
    for i, score in enumerate(extraction):
        score = extraction[i]
        name = score['FileName'][0]
        score.to_csv(dest + name + '_windows.csv')