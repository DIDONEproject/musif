import os
from musif.extract import score
from musif import FeaturesExtractor, config
from musif.reports.generate import FeaturesGenerator

if __name__ == "__main__":
    parts = ["obI", "obII", "VnI"]
    parts = None
    # NEW component for filtering parts

    df = FeaturesExtractor().from_file(
        "arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", parts)
    # level=FeaturesExtractor.level
    path = '.'
    import pandas as pd
    # df = pd.read_csv('./myfeatures.csv')
    FeaturesGenerator().generate_reports(df, 1, path)  # parts)  # level=level)
