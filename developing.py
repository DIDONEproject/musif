import os
from musif.extract import score
from musif import FeaturesExtractor, config
from musif.reports.generate import FeaturesGenerator

if __name__ == "__main__":
    parts = ["obI", "obII", "VnI"]
    parts = None
    # NEW component for filtering parts

    df = FeaturesExtractor("config.yml").from_file(
        "arias/xml/Dem02M-In_te-1733-Caldara[1.02][0417].xml", parts)
    # level=FeaturesExtractor.level
    path = '.'
    import pandas as pd
    # df = pd.read_csv('./myfeatures.csv')
    FeaturesGenerator().generate_reports(df, 1, path, parts)  # level=level)
