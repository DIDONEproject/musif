from musif import FeaturesExtractor, FilesValidator

if __name__ == "__main__":

    parts_filter = ["vnI", "vnII", "va", "bs", "sop", "ten", "alt", "bar", "bass", "bbar"]

    arias_dir = "../../Corpus/xml"
    musescore_dir = "../../Corpus/mscx"
    # FilesValidator("config.yml", parallel=True).validate(arias_dir)
    df_scores = FeaturesExtractor("config.yml").extract(arias_dir, musescore_dir, parts_filter=parts_filter)
    # df_scores.to_csv("myfeatures.csv", index=False)
