from musif.common.utils import read_dicts_from_csv, write_dicts_to_csv

if __name__ == "__main__":

    arias_scoring = read_dicts_from_csv("data/arias_scoring.csv")

    arias_metadata = [
        {
            "id": aria["id"],
            "label": aria["opera"][:3],
            "name": aria["aria"],
            "year": aria["year"],
            "composer": aria["composer"],
            "librettist": aria["opera"][-1],
            "act": aria["Act"],
            "scene": aria["Scene"],
            "act_scene": aria["Act&Scene"],
            "form": aria["Form"],
            "character": aria["Character"],
            "type": aria["Type"],
            "city": aria["City"],
            "country": aria["Country"],
        } for aria in arias_scoring
    ]
    arias_metadata = sorted(arias_metadata, key=lambda aria: aria["id"])
    write_dicts_to_csv(arias_metadata, "data/arias_metadata.csv")

    print()
