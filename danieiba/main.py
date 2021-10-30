from musif import FeaturesExtractor

if __name__ == "__main__":

    parts_filter = ["vnI"]

    df_scores = FeaturesExtractor("config.yml").extract("../../Corpus/xml/Dem18M-La_destra-1743-Gluck[2.12][0606].xml", parts_filter=parts_filter)
    print()
