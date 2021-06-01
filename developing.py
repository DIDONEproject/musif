import os

from musif import FeaturesExtractor, config
from musif.reports.generate import FeaturesGenerator
import pandas as pd
if __name__ == "__main__":
    parts = ["vnI"] #"obI"]
    # parts = None

    arias_path="./arias/"

    # arias_path="./arias/10arias"

    df = FeaturesExtractor("config.yml", require_harmonic_analysis = False).from_dir(arias_path, parts)

    # df.to_csv('datitos.csv', index=False, encoding='utf8', compression=None)   
    # df = pd.read_csv('datitos.csv', encoding='utf-8', engine='python', float_precision=None,  dtype=str)
    path = '.'

    FeaturesGenerator().generate_reports(df, 1, path, parts) 
