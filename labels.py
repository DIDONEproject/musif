from glob import glob
from os import path

from musif.common.utils import read_dicts_from_csv, write_dicts_to_csv

if __name__ == "__main__":

    passions = read_dicts_from_csv("passions.csv")
    data_by_label = {label_data["Label"]: label_data for label_data in passions}
    label_rows = []
    for file_path in glob("../Corpus/xml/*.xml"):
        file_name = path.basename(file_path)
        aria_label = str(file_name.split("-", 2)[0])
        aria_id = file_name.split("[")[-1].split("]")[0]
        label_data = data_by_label.get(aria_label)
        if label_data is None:
            print(aria_label + " not found.")
            continue
        label_row = {
            "AriaId": aria_id,
            "Label_BasicPassion": label_data["Basic_passion"],
            "Label_Passions": label_data["Passion"],
            "Label_Sentiment": label_data["Value"],
            "Label_Time": label_data["Time"],
        }
        label_rows.append(label_row)
    print()
    labels_metadata = sorted(label_rows, key=lambda aria: aria["AriaId"])
    write_dicts_to_csv(labels_metadata, "labels.csv")
