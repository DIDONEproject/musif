from musif import FeaturesExtractor
from musif.extract.extract import FilesValidator

if __name__ == "__main__":

    didone_filter = ["vnI", "vnII", "va", "bs", "sop", "ten", "alt", "bar", "bass", "bbar"]
    test_filter = ["obI"]

    # FilesValidator("config.yml").validate("arias/xml")
    df_scores = FeaturesExtractor("config.yml", sequential=True).extract("arias/xml", parts_filter=didone_filter)
    df_scores.to_csv("myfeatures.csv", index=False)
