from musif.extract import score
from musif import FeaturesExtractor, config
from musif.reports.generate import FeaturesGenerator

if __name__ == "__main__":
    # df, _ = FeaturesExtractor().from_file("arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", ["obI", "obII"])
    path = './results/'
    import pandas as pd
    df = pd.read_csv('./intermediate.csv')
    FeaturesGenerator().generate_reports(df, 1, path)
