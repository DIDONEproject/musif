from musif import FeaturesExtractor

if __name__ == "__main__":

    df_scores = FeaturesExtractor("config.yml").extract()
    print()
