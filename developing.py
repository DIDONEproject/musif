import sys

from musif.extract.extract import FeaturesExtractor
from musif.reports.generate import FeaturesGenerator
import pandas as pd
sys.path.insert(0, "../musif")
sys.path.insert(0, "../musif/musif") 


if __name__ == "__main__":
# 
    data_dir = r'tests/data/static/features'
    # data_dir = r'arias/error/'
    # 
    df = FeaturesExtractor("martiser/config.yml", data_dir=data_dir).extract()

    df.to_csv('martiser/dataframe.csv', index=False)
    df=pd.read_csv('martiser/dataframe.csv')
    path = './'
    FeaturesGenerator("martiser/myconfig.yml").generate_reports(df, path, num_factors=1, visualizations=True)
    