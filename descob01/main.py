
from musif import FeaturesExtractor


if __name__ == "__main__":

    didone_filter = ["vnI","va", "bs", "sop", "ten", "alt", "bar", "bass", "bbar"]
    df_scores = FeaturesExtractor("config.yml").extract("../arias/Dem02M-In_te-1733-Caldara[1.02][0417].xml",
                                                        parts_filter=didone_filter)

    print(df_scores["Score_RhythmInt"])
