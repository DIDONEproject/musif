from copy import deepcopy

from musif.common.utils import read_dicts_from_csv, write_dicts_to_csv

if __name__ == "__main__":

    arias_scoring = read_dicts_from_csv("myfeatures_400.csv")
    labels = read_dicts_from_csv("metadata/score/labels.csv")
    labels2 = []
    data_by_label = {label_data["Label"]: label_data for label_data in labels}

    for aria_data in arias_scoring:
        label_data = data_by_label.get(aria_data["AriaLabel"])
        if label_data is None:
            print(aria_data["AriaLabel"] + " not found.")
            continue
        label2 = {
            "AriaId": aria_data["AriaId"],
            "Label_BasicPassion": label_data["Basic_passion"],
            "Label_Passions": label_data["Passion"],
            "Label_Sentiment": label_data["Value"],
            "Label_Time": label_data["Time"],
        }
        labels2.append(label2)
    print
    labels_metadata = sorted(labels2, key=lambda aria: aria["AriaId"])
    write_dicts_to_csv(labels_metadata, "metadata/score/labels.csv")
    # arias_scoring = read_dicts_from_csv("data/arias_scoring.csv")

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

    print()
