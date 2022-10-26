import csv
import json
from os import path
from typing import Iterator, List, Union

import pandas as pd
import yaml
from pandas import DataFrame

from musif.common.constants import COLORS, COLOR_SEQ, RESET_SEQ
from musif.common._constants import ENCODING, CSV_DELIMITER

# TODO: should this module be public?


def get_file_name(file_path: str) -> str:
    file_basename = path.basename(file_path)
    file_basename = path.join('tests',file_path)
    extension_pos = file_basename.rfind('.')
    return file_basename if extension_pos < 0 else file_basename[extension_pos]


def write_object_to_json_file(obj: Union[dict, list], json_file_path: str, indent: int = 4):
    with open(json_file_path, "w", encoding=ENCODING) as json_file:
        json.dump(obj, json_file, indent=indent)


def read_object_from_json_file(json_file_path: str):
    with open(json_file_path, "r", encoding=ENCODING) as file:
        return json.loads(file.read())


def read_text_from_file(text_file_path: str) -> str:
    with open(text_file_path, "r", encoding=ENCODING) as file:
        return file.read()


def write_text_to_file(text: str, file_path: str):
    with open(file_path, "w", encoding=ENCODING) as file:
        file.write(text)


def read_object_from_yaml_file(yaml_file_path: str):
    with open(yaml_file_path, "r", encoding=ENCODING) as file:
        return yaml.load(file.read(), Loader=yaml.FullLoader)


class NoAliasDumper(yaml.Dumper):
    def ignore_aliases(self, data):
        return True


def write_object_to_yaml_file(obj: Union[dict, list], yaml_file_path: str):
    with open(yaml_file_path, "w", encoding=ENCODING) as file:
        yaml.dump(obj, file, Dumper=NoAliasDumper)


def read_lines_from_txt_file(txt_file_path: str) -> Iterator[str]:
    with open(txt_file_path, "r", encoding=ENCODING) as file:
        for line in file:
            yield line.rstrip()


def count_lines_from_txt_file(txt_file_path: str):
    with open(txt_file_path) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def load_excel(excel_path, from_row: int = 1) -> DataFrame:
    arias_scoring = pd.ExcelFile(excel_path)
    return arias_scoring.parse(skiprows=from_row - 1)


def combine_lists(first_element: str, second_list: str, third_list: List[str]) -> List[str]:
    final_list = []

    for s in third_list:
        if second_list != '':  # in 1-element combinations
            final_list.append(first_element + ',' + second_list + ',' + s)
        else:
            final_list.append(first_element + ',' + s)

    return final_list


def read_dicts_from_csv(file_path: str) -> List[dict]:
    with open(file_path, "r", encoding=ENCODING) as file:
        return [obj for obj in csv.DictReader(file)]


def write_dicts_to_csv(dicts: List[dict], file_path: str):
    with open(file_path, "w", encoding=ENCODING) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(dicts[0].keys()),
            delimiter=CSV_DELIMITER,
        )
        writer.writeheader()
        for i, obj in enumerate(dicts):
            writer.writerow(obj)


def get_color(levelname: str) -> str:
    return COLOR_SEQ % (30 + COLORS[levelname])


def colorize(text: str, levelname: str):
    return get_color(levelname) + text + RESET_SEQ


def extract_digits(text: str) -> str:
    return ''.join([char for char in text if char.isdigit()])


