import sys
sys.path.insert(0, "../musif/")
# sys.path.append('../')
from musif.extract.extract import FeaturesExtractor
# from musif.reports.generate import ReportsGenerator

import pandas as pd

if __name__ == "__main__":

    data_dir = r'tests/data/static/features'
    musescore_dir=data_dir

    data_dir = r'../../_Ana/Music Analysis/xml/corpus_github\xml/Ale05M-O_sugli-1740-Caballone[1.05][1139].xml'
    
    #reference
    # data_dir = r'../../_Ana/Music Analysis/xml/corpus_github\xml/Did03M-Son_regina-1724-Sarro[1.05][0001].xml'

    musescore_dir = r'../../_Ana\Music Analysis/xml/corpus_github/musescore'
    
    df = FeaturesExtractor("scripts/config_tests.yml", data_dir=data_dir, musescore_dir=musescore_dir).extract()
    # df.to_csv('testew.csv', index=False)
    # df=pd.read_csv('martiser/dataframe.csv')
    # path = './'
    # ReportsGenerator("martiser/myconfig.yml").generate_reports(df, path, num_factors=1, visualizations=True)
    print('asd')