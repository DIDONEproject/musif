import sys
sys.path.insert(0, "../musif/")
# sys.path.append('../')
from musif.extract.extract import FeaturesExtractor
from musif.reports.generate import ReportsGenerator
from musif.process.processor import DataProcessor

import pandas as pd

if __name__ == "__main__":
    data_dir = r'tests/data/static/features'
    musescore_dir=data_dir

    data_dir = r'../../_Ana/Music Analysis/xml/corpus_github\xml/Did01M-Dovrei_ma-1762-Sarti[1.02][0257].xml'
    
    musescore_dir = r'../../_Ana\Music Analysis/xml/corpus_github/musescore'
    
    df = FeaturesExtractor("scripts/config_tests.yml", data_dir=data_dir, musescore_dir=musescore_dir).extract()
    df.to_csv('martiser/'+'test.csv', index=False)
    # df=pd.read_csv('arias_test.csv')
    path = '.'
    # ReportsGenerator("scripts/config_tests.yml").generate_reports(df, path, num_factors=0, visualizations=True)
    
    