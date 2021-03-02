from musif.common.utils import read_dicts_from_csv, write_dicts_to_csv

if __name__ == "__main__":

    # arias_scoring = read_dicts_from_csv("data/arias_metadata.csv")

    # operas = {
    #     (aria["opera"][:3], aria["year"], aria["composer"]): {
    #         "opera": aria["opera"][:3],
    #         "year": aria["year"],
    #         "composer": aria["composer"],
    #         "librettist": aria["opera"][-1],
    #         "city": aria["City"],
    #         "country": aria["Country"]
    #     } for aria in arias_scoring
    # }
    # operas = sorted(operas.values(), key=lambda aria: (aria["opera"][:3], aria["year"], aria["composer"]))
    # write_dicts_to_csv(operas, "data/operas.csv")

    # arias_metadata = [
    #     {
    #         "id": aria["id"],
    #         "label": aria["opera"][:3],
    #         "name": aria["aria"],
    #         "year": aria["year"],
    #         "composer": aria["composer"],
    #         "librettist": aria["opera"][-1],
    #         "act": aria["Act"],
    #         "scene": aria["Scene"],
    #         "act_scene": aria["Act&Scene"],
    #         "form": aria["Form"],
    #         "character": aria["Character"],
    #         "type": aria["Type"],
    #         "city": aria["City"],
    #         "country": aria["Country"],
    #     } for aria in arias_scoring
    # ]
    # arias_metadata = sorted(arias_metadata, key=lambda aria: aria["id"])
    # write_dicts_to_csv(arias_metadata, "data/arias_metadata.csv")

    # clefs = read_dicts_from_csv("data/arias_clefs.csv")
    # arias_metadata = read_dicts_from_csv("data/arias_metadata.csv")
    # for aria_data, clefs_data in zip(arias_metadata, clefs):
    #     assert aria_data["id"] == clefs_data["id"]
    #     aria_data["clef1"] = clefs_data["Clef 1"]
    #     aria_data["clef2"] = clefs_data["Clef 2"]
    #     aria_data["clef3"] = clefs_data["Clef 3"]
    # write_dicts_to_csv(arias_metadata, "data/arias_metadata.csv")

    print()
