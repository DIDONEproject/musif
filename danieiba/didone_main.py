from musif import FeaturesExtractor, FilesValidator
from musif.common._utils import extract_digits

if __name__ == "__main__":

    # FilesValidator("didone_config.yml").validate()
    df_scores = FeaturesExtractor("didone_config.yml").extract()
    # df_scores.to_csv("myfeatures.csv", index=False)
