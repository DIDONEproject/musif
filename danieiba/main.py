from musif import FeaturesExtractor, FilesValidator

if __name__ == "__main__":

    # FilesValidator("config.yml").validate()
    df_scores = FeaturesExtractor("config.yml").extract()
    df_scores.to_csv("myfeatures.csv", index=False)
    print()
