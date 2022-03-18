import sys
sys.path.insert(0, "../musif/")
# sys.path.append('../')
from musif.extract.extract import FeaturesExtractor
# from musif.reports.generate import ReportsGenerator

import pandas as pd

if __name__ == "__main__":

    data_dir = r'tests/data/static/features'
    musescore_dir=data_dir

    # data_dir = r'../Corpus_175/xml/Ale02M-Vedrai_con-1772-Anfossi[1.02][0811].xml'
    # musescore_dir =  r'../Corpus_175/musescore'
    
    #reference
    # data_dir = r'../../_Ana/Music Analysis/xml/corpus_github\xml/Did03M-Son_regina-1724-Sarro[1.05][0001].xml'

    musescore_dir = r'../../_Ana\Music Analysis/xml/corpus_github/musescore'
    df = FeaturesExtractor("scripts/config.yml", data_dir=data_dir, musescore_dir=musescore_dir).extract()
    df.to_csv('analyzed_Did03M-Son_regina-1730-Sarro[1.05][0006].csv', index=False)
    # df=pd.read_csv('martiser/dataframe.csv')
    # path = './'
    # ReportsGenerator("martiser/myconfig.yml").generate_reports(df, path, num_factors=1, visualizations=True)
    print('asd')