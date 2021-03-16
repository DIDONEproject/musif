from musif import FeaturesExtractor

if __name__ == "__main__":

    df = FeaturesExtractor().from_file("arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", ["obI", "obII"])
    print(df)
