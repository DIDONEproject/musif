from musif.extract.extract import FeaturesExtractor

if __name__ == "__main__":
    df = FeaturesExtractor("config.yml").extract()
    print(df["Score_DynMean"].values[0])
    print("hello")
