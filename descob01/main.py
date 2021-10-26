
from musif import FeaturesExtractor
from musif.extract.features.prefix import get_score_prefix
from musif.extract.features.dynamics import DYNMEAN, DYNGRAD, DYNABRUPTNESS


if __name__ == "__main__":
    didone_filter = ["vnI","va", "bs", "sop", "ten", "alt", "bar", "bass", "bbar"]
    df_scores = FeaturesExtractor("config.yml").extract("../arias/Dem01M-O_piu-1735-Leo[1.01][0430].xml",
                                                        parts_filter=didone_filter)
    prefix = get_score_prefix()
    #print(df_scores.get(f"{prefix}{RHYTHMINT}"))
    #print(df_scores.get(f"{prefix}{RHYTHMINTSEP}"))
    print(df_scores.get(f"{prefix}{DYNMEAN}"))
    print(df_scores.get(f"{prefix}{DYNGRAD}"))
    print(df_scores.get(f"{prefix}{DYNABRUPTNESS}"))
