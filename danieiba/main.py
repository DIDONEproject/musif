from musif import FeaturesExtractor

if __name__ == "__main__":

    parts_filter = ["obI"]

    df_scores = FeaturesExtractor("config.yml").extract("../../Corpus/xml", parts_filter=parts_filter)
    print()
