import sys

from musif.extract.extract import FeaturesExtractor, FilesValidator
from musif.reports.generate import FeaturesGenerator
import pandas as pd
sys.path.insert(0, "../musif")
sys.path.insert(0, "../musif/musif") 


if __name__ == "__main__":
 
    data_dir = r'tests/data/static/features'
    # data_dir = r'../Corpus_drive400/xml/Ale07M-Se_mai-1752-Perez[1.07][1059].xml'
    musescore_dir=data_dir
    
    
    data_dir = r'../../_Ana/Music Analysis/xml/corpus_github\xml/Did18M-Ah_non_lasciarmi-1784-Andreozzi[X.XX][0375].xml'
    musescore_dir = r'../../_Ana\Music Analysis/xml/corpus_github/musescore'



    df = FeaturesExtractor("scripts/config_drive.yml", data_dir=data_dir, musescore_dir=musescore_dir).extract()

    df.to_csv('test.csv', index=False)
    # df=pd.read_csv('martiser/dataframe.csv')
    # path = './'
    # FeaturesGenerator("martiser/myconfig.yml").generate_reports(df, path, num_factors=1, visualizations=True)
    