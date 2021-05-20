import os

from musif import FeaturesExtractor, config
from musif.reports.generate import FeaturesGenerator

if __name__ == "__main__":
    parts = ["vnI","obI"]
    # parts = None
    arias_path="./arias/xml/"
    # arias_path="./arias/10arias"
    # df = FeaturesExtractor("config.yml").from_file(
    #     "arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", parts)
    df = FeaturesExtractor("config.yml").from_dir(arias_path, parts)
    path = '.'
    import pandas as pd
    FeaturesGenerator().generate_reports(df, 1, path, parts) 
