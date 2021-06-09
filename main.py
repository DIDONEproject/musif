from musif import FeaturesExtractor

if __name__ == "__main__":

    didone_filter = ["vnI", "vnII", "va", "bs", "sop", "ten", "alt", "bas"]
    test_filter = ["obI"]

    df_scores = FeaturesExtractor("config.yml", sequential=True).from_dir(
        "/home/daniel/clients/didone/projects/Corpus/xml",
        parts_filter=didone_filter,
    )
    df_scores.to_csv("myfeatures.csv", index=False)

    # df1 = FeaturesExtractor({"split": True, "data_dir": "data"}).from_file("arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", ["obI", "obII"])
    # df2 = FeaturesExtractor(split=True, data_dir="data").from_file("arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", ["obI", "obII"])
    # df3 = FeaturesExtractor("/home/daniel/clients/didone/projects/musiF/config.yml").from_file("arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", ["obI", "obII"])
    # df4 = FeaturesExtractor("config.yml").from_file("arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", ["obI", "obII"])

