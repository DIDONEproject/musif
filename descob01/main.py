
from musif import FeaturesExtractor
from musif.extract.features.prefix import get_score_prefix
from musif.extract.features.custom.rhythm import RHYTHMINT, RHYTHMINTSEP


if __name__ == "__main__":

    didone_filter = ["vnI","va", "bs", "sop", "ten", "alt", "bar", "bass", "bbar"]
    df_scores = FeaturesExtractor("config.yml").extract("../arias/Dem02M-In_te-1733-Caldara[1.02][0417].xml",
                                                        parts_filter=didone_filter)
    prefix = get_score_prefix()
    print(df_scores.get(f"{prefix}{RHYTHMINT}"))
    print(df_scores.get(f"{prefix}{RHYTHMINTSEP}"))
