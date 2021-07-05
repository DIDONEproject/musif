import os

from musif import FeaturesExtractor, config
from musif.reports.generate import FeaturesGenerator
import pandas as pd

if __name__ == "__main__":
    parts = ["vnI","obI"]
    # parts = None

    arias_path="./arias/"
    # arias_path="./arias/10arias"

    df = FeaturesExtractor("config.yml").extract(arias_path, parts)
    path = './'

    FeaturesGenerator("config.yml").generate_reports(df, 1, path, parts) 
