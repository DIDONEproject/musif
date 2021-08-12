from musif import FeaturesExtractor
from musif.reports.generate import FeaturesGenerator

if __name__ == "__main__":
    parts = ["vnI","obI"]
    # parts = None

    arias_path="./arias/"
    # arias_path="../Corpus/subcorpus"
    # os.remove("failed_files.txt")
    df = FeaturesExtractor("myconfig.yml").extract(arias_path, parts)
    path = './'
    FeaturesGenerator("myconfig.yml").generate_reports(df, 1, path, parts) 
