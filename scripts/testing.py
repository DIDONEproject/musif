import os
import sys
sys.path.insert(0, "../musif/")
# sys.path.append('../')
from musif.extract.extract import FeaturesExtractor
from musif.reports.generate import ReportsGenerator
from musif.process.processor import DataProcessor

import pandas as pd

dest= 'martiser/'

def save_windows_dfs(dest, extraction) -> None:
    dest = dest + 'windows_extraction/'
    if not os.path.exists(dest):
        os.mkdir(dest)
    for i, score in enumerate(extraction):
        score = extraction[i]
        name = score['FileName'][0]
        score.to_csv(dest + name + '_windows.csv')

if __name__ == "__main__":
    data_dir = r'tests/data/static/features'
    musescore_dir=data_dir

    data_dir = r'../../_Ana/Music Analysis/xml/corpus_github\xml/Did29M-A_trionfar-1763-Traetta[3.07][1403].xml'
    musescore_dir = r'../../_Ana\Music Analysis/xml/corpus_github/musescore'
    
    extrac = FeaturesExtractor("scripts/config_tests.yml", data_dir = data_dir, musescore_dir=musescore_dir).extract()
    if type(extrac)==list:
        save_windows_dfs(dest, extrac)
    else:
        extrac.to_csv(dest + 'test.csv', index=False)
    
    # extrac=pd.read_csv('arias_test.csv')
    path = '.'
    # ReportsGenerator("scripts/config_tests.yml").generate_reports(extraction, path, num_factors=0, visualizations=True)
    
