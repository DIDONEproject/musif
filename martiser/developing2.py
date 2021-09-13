from musif import FeaturesExtractor
from musif.reports.generate import FeaturesGenerator
import os

if __name__ == "__main__":
    parts = ["vnI","obI"]
    # parts = None

    arias_path= "../arias/"
    # arias_path="../Corpus/subcorpus2"
    # arias_path="../Corpus/fallido"

    if os.path.exists("failed_files.txt"):
        os.remove("failed_files.txt")
    df = FeaturesExtractor("myconfig2.yml").extract(arias_path, parts)
    path = '../'
    FeaturesGenerator("myconfig2.yml").generate_reports(df, 1, path, parts) 
