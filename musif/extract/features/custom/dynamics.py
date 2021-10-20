from typing import List

from musif.config import Configuration
from musif.extract.constants import DATA_SCORE
from musif.extract.features.core import DATA_NOTES

DYNMEAN = "DynMean"


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    result=0
    for elem in part_data["measures"]:
        for measure in elem.elements:
            m = measure.get("Dynamic")#Voy por aqui, sacar clase, si es dynamic saco valor
            if m is not None:
                result = result+m

    part_features.update({
        DYNMEAN: result
    })
    pass


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict],
                         score_features: dict):
    score = score_data[DATA_SCORE]
    e = score.elements
    print(score)
    for elem in score.elements:
        if elem.id == "Violino I":
            v = elem
            break

    d = v.elements
    #sea un diccionario de todos los dynamic mean
    score_features.update({
        DYNMEAN: e
    })
