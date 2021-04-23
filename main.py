from musif import FeaturesExtractor

if __name__ == "__main__":

    parts = ["flII", "obI", "bn", "hnI", "hnII", "ten"]
    df_scores = FeaturesExtractor("config.yml").extract("arias/xml", parts_filter=parts)
    df_scores.to_csv("myfeatures.csv", index=False)

    # df1 = FeaturesExtractor({"split": True, "data_dir": "data"}).from_file("arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", ["obI", "obII"])
    # df2 = FeaturesExtractor(split=True, data_dir="data").from_file("arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", ["obI", "obII"])
    # df3 = FeaturesExtractor("/home/daniel/clients/didone/projects/musiF/config.yml").from_file("arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", ["obI", "obII"])
    # df4 = FeaturesExtractor("config.yml").from_file("arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", ["obI", "obII"])

