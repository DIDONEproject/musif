from math import floor
from typing import List

from music21.stream import Measure, Score

from musif.config import Configuration
from musif.extract.constants import DATA_MUSESCORE_SCORE, DATA_SCORE
from .constants import END_OF_THEME_A

def update_score_objects(
    score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict
):
    score: Score = score_data[DATA_SCORE]
    last_measure = floor(float(score_features.get(END_OF_THEME_A, "1000000")))

    for part in score.parts:
        read_measures = 0
        elements_to_remove = []
        for measure in part.getElementsByClass(Measure):  # type: ignore
            read_measures += 1
            if read_measures > last_measure:
                elements_to_remove.append(measure)
        part.remove(targetOrList=elements_to_remove)  # type: ignore
    if cfg.is_requested_musescore_file() and score_data[DATA_MUSESCORE_SCORE] is not None:
        score_data[DATA_MUSESCORE_SCORE] = score_data[DATA_MUSESCORE_SCORE].loc[score_data[DATA_MUSESCORE_SCORE]['mn'] <= last_measure]
        score_data[DATA_MUSESCORE_SCORE].reset_index(inplace=True, drop=True)
def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    pass
