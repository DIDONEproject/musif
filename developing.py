import os
from musif import FeaturesExtractor, config
from musif.reports.generate import FeaturesGenerator

if __name__ == "__main__":
    parts = ["obI"]#, "obII"]
    # parts = None
    # df = FeaturesExtractor("config.yml").from_file(
    #     "arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", parts)
    df = FeaturesExtractor("config.yml").from_dir(
        "./arias/xml/", parts)
    path = '.'
    import pandas as pd
    FeaturesGenerator().generate_reports(df, 1, path, parts) 
