import sys
sys.path.insert(0, "../musif/")
from musif.extract.extract import FeaturesExtractor
# from musif.reports.generate import ReportsGenerator

import pandas as pd

if __name__ == "__main__":

    data_dir = r'tests/data/static/features'
    musescore_dir=data_dir
    
    prev=r'../Corpus'
    data_dir = prev+r'/xml/'
    # test this file for not found mscsx: Ale61X-Paventa_del-1792-Piccinni[2.08][0880]
    
    #reference
    # data_dir = r'../../_Ana/Music Analysis/xml/corpus_github\xml/Did03M-Son_regina-1724-Sarro[1.05][0001].xml'

    musescore_dir = prev+r'/musescore/'
    
    df = FeaturesExtractor("scripts/config.yml", data_dir=data_dir, musescore_dir=musescore_dir).extract()
    # df.to_csv('test.csv', index=False)
    # df=pd.read_csv('martiser/dataframe.csv')
    # path = './'
    # ReportsGenerator("martiser/myconfig.yml").generate_reports(df, path, num_factors=1, visualizations=True)
    print('asd')