from statistics import mean
from typing import List

from musif.config import Configuration
from musif.extract.features.prefix import get_score_prefix
from musif.musicxml.tempo import get_number_of_beats

DYNMEAN = "DynMean"
DYNMEAN_WEIGHTED = "DynMean_weighted"
DYNABRUPTNESS = "DynAbruptness"
DYNGRAD = "DynGrad"

DYNAMIC_VALUES = {"ff": 101, "più f": 96, "f assai": 94, "f": 88, "poco f": 80, "mf": 75, "mp": 62, "p": 49,
                  "dolce": 49, "p assai": 42, "pp": 36, "soto voce": 36}


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    dynamics = []
    beats_section = 0
    dyn_mean_weighted = 0
    total_beats = 0
    dyn_grad = 0
    last_dyn = 0
    beat = 1
    for bar_section in part_data["measures"]:
        for measure in bar_section.elements:
            if measure.classes[0] == "Dynamic":  # need to change with beat count and beat being different
                position = get_position(beat_count, beat, measure.beat)
                old_beat = position - 1  # if change in beat 1.5, remaining old beats 0.5
                dyn_mean_weighted += (beats_section + old_beat) * last_dyn
                new_dyn = get_dynamic_numeric(measure.value)
                dynamics.append(new_dyn)  # also could get a value (0,1) with volumeScalar
                if (beats_section + old_beat) > 0:
                    dyn_grad += (new_dyn - last_dyn) / (beats_section + old_beat)
                last_dyn = new_dyn
                beats_section = - old_beat  # number of beats that has old dynamic
            elif measure.classes[0] == "TimeSignature":
                beat_count = measure.beatCount
                beat = get_number_of_beats(measure.ratioString)
        beats_section += beat
        total_beats += beat

    dyn_mean_weighted += beats_section * dynamics[-1] if len(dynamics) != 0 else 0

    part_features.update({
        DYNMEAN: mean(dynamics) if len(dynamics) != 0 else 0,
        DYNMEAN_WEIGHTED: dyn_mean_weighted / total_beats,
        DYNGRAD: dyn_grad / (len(dynamics) - 1) if len(dynamics) > 1 else 0,
        DYNABRUPTNESS: dyn_grad / (total_beats - beats_section) if (total_beats - beats_section) > 0 else 0
    })


def get_dynamic_numeric(value):
    if value in DYNAMIC_VALUES:
        return DYNAMIC_VALUES.get(value)
    else:
        return 0


def get_position(beat_count, beat, pos):
    if beat == beat_count:
        return pos
    else:
        return (pos / beat_count) + beat


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict],
                         score_features: dict):
    prefix = get_score_prefix()
    dic_dyn_mean = dict()
    dic_dyn_mean_weighted = dict()
    dic_dyn_grad = dict()
    dic_dyn_abrup = dict()
    for part in parts_features:
        dic_dyn_mean.update({part["PartAbbreviation"]: part[DYNMEAN]})
        dic_dyn_mean_weighted.update({part["PartAbbreviation"]: part[DYNMEAN_WEIGHTED]})
        dic_dyn_grad.update({part["PartAbbreviation"]: part[DYNGRAD]})
        dic_dyn_abrup.update({part["PartAbbreviation"]: part[DYNABRUPTNESS]})

    score_features.update({
        f"{prefix}{DYNMEAN}": dic_dyn_mean,
        f"{prefix}{DYNMEAN_WEIGHTED}": dic_dyn_mean_weighted,
        f"{prefix}{DYNGRAD}": dic_dyn_grad,
        f"{prefix}{DYNABRUPTNESS}": dic_dyn_abrup
    })
