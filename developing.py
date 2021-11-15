import sys
from musif.extract.extract import FeaturesExtractor
from musif.reports.generate import FeaturesGenerator
import pandas as pd
sys.path.insert(0, "../musif")
sys.path.insert(0, "../musif/musif") 


if __name__ == "__main__":


    # arias_path="./tests/data/static/"
<<<<<<< HEAD
    arias_path="./arias"
    # arias_path="./arias/error/"
=======
    # arias_path="./arias/prueba/"

    # arias_path="./arias/error"
>>>>>>> 0e32e5f (Fix harmony excel)

    # df = FeaturesExtractor("martiser/myconfig.yml").extract()
    # df.to_csv('martiser/dataframe.csv', index=False)

    df=pd.read_csv('martiser/dataframe.csv')

    parts = ["vnI", "obI", "ten"]
    path = './'
    FeaturesGenerator("martiser/myconfig.yml").generate_reports(df, path, num_factors=1, visualizations=False)