from statistics import mean
from typing import List

from musif.config import Configuration
from musif.extract.features.prefix import get_score_prefix

DYNMEAN = "DynMean"

DYNAMIC_VALUES = {"ff": 101, "più f": 96, "f assai": 94, "f": 88, "poco f": 80, "mf": 75, "mp": 62, "p": 49,
                  "dolce": 49, "p assai": 42, "pp": 36, "soto voce": 36}


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    dynamics = []
    for elem in part_data["measures"]:
        for measure in elem.elements:
            if measure.classes[0] == "Dynamic":
                dynamics.append(DYNAMIC_VALUES.get(measure.value))  # also could get a value (0,1) with volumeScalar

    part_features.update({
        DYNMEAN: mean(dynamics) if len(dynamics) != 0 else 0
    })


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict],
                         score_features: dict):
    prefix = get_score_prefix()
    dic = dict()
    for part in parts_features:
        dic.update({part["PartAbbreviation"]: part[DYNMEAN]})

    score_features.update({
        f"{prefix}{DYNMEAN}": dic
    })
