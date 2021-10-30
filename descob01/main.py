
from musif import FeaturesExtractor
from musif.extract.features.prefix import get_score_prefix
from musif.extract.features.dynamics import DYNMEAN, DYNGRAD, DYNABRUPTNESS
from musif.extract.features.rhythm import DOTTEDRHYTHM,DOUBLE_DOTTEDRHYTHM


if __name__ == "__main__":
    didone_filter = ["vnI","va", "bs", "sop", "ten", "alt", "bar", "bass", "bbar"]
    df_scores = FeaturesExtractor("config.yml").extract(["../musif/tests/data/arias_test","../musif/tests/data/arias_test1"],
                                                        parts_filter=didone_filter)
    prefix = get_score_prefix()
    #print(df_scores.get(f"{prefix}{RHYTHMINT}"))
    #print(df_scores.get(f"{prefix}{RHYTHMINTSEP}"))
    print(df_scores.get(f"{prefix}{DYNMEAN}"))
    print(df_scores.get(f"{prefix}{DYNGRAD}"))
    #print(df_scores.get(f"{prefix}{DYNABRUPTNESS}"))
    #print(df_scores.get(f"{prefix}{DOTTEDRHYTHM}"))
    #print(df_scores.get(f"{prefix}{DOUBLE_DOTTEDRHYTHM}"))
