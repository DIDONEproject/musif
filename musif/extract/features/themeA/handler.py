from math import floor
from typing import List

from music21.stream import Measure, Score

from musif.config import Configuration
from musif.extract.constants import DATA_SCORE, HARMONY_FEATURES


def update_score_objects(
    score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict
):
    score: Score = score_data[DATA_SCORE]
    last_measure = floor(float(score_features.get("EndOfThemeA", "1000000")))

    for part in score.parts:
        read_measures = 0
        elements_to_remove = []
        for measure in part.getElementsByClass(Measure):
            read_measures += 1
            if read_measures > last_measure:
                elements_to_remove.append(measure)
        part.remove(targetOrList=elements_to_remove)
    if cfg.is_requested_feature_category(HARMONY_FEATURES):
        score_data['MS3_score'] = score_data['MS3_score'].loc[score_data['MS3_score']['mn'] <= last_measure]


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    pass
