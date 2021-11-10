from math import floor
from typing import List

from music21.stream import Measure, Score

from musif.config import Configuration
from musif.extract.constants import DATA_SCORE


def update_score_objects(
    score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict
):
    score: Score = score_data[DATA_SCORE]
    end_of_theme_a = floor(float(score_features.get("EndOfThemeA", "1000000").replace(",", ".")))
    for part in score.parts:
        elements_to_remove = []
        for i in range(len(part.elements)):
            elem = part.elements[i]
            if len(elements_to_remove) > 0:
                elements_to_remove.append(elem)
            elif isinstance(elem, Measure) and elem.number >= end_of_theme_a:
                elements_to_remove.append(elem)
        part.remove(targetOrList=elements_to_remove)


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    pass
