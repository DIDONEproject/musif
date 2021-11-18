from math import ceil, floor
from typing import List

from music21 import Music21Object
from music21.stream import Measure, Score

from musif.config import Configuration
from musif.extract.constants import DATA_SCORE


def update_score_objects(
    score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict
):
    score: Score = score_data[DATA_SCORE]
    end_of_theme_a = float(score_features.get("EndOfThemeA", "1000000"))
    last_measure = ceil(end_of_theme_a)
    last_whole_measure = floor(end_of_theme_a)
    last_measure_fraction = end_of_theme_a - last_whole_measure

    for part in score.parts:
        read_measures = 0
        elements_to_remove = []
        for measure in part.getElementsByClass(Measure):
            read_measures += 1
            if read_measures > last_measure:
                elements_to_remove.append(measure)
        part.remove(targetOrList=elements_to_remove)
        if last_measure != last_whole_measure:
            measure: Measure = part.measure(last_measure)
            fractioned_elements = get_fractioned_elements_to_remove(part.measure(last_measure), last_measure_fraction)
            measure.remove(targetOrList=fractioned_elements)
            pass


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    pass


def get_fractioned_elements_to_remove(measure: Measure, measure_fraction_to_keep: float) -> List[Music21Object]:
    number_of_beats = measure.duration.ordinal
    max_allowed_beat = measure_fraction_to_keep * number_of_beats
    elements = list(measure.elements)
    elements_to_remove = [elem for elem in elements if elem.beat > max_allowed_beat]
    return elements_to_remove
