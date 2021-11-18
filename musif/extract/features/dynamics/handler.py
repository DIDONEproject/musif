from statistics import mean
from typing import List

from musif.config import Configuration
from musif.extract.features.prefix import get_score_prefix
from musif.extract.utils import get_beat_position
from musif.musicxml.tempo import get_number_of_beats

from .constants import *


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    dynamics = []
    beats_section = 0
    dyn_mean_weighted = 0
    total_beats = 0
    dyn_grad = 0
    last_dyn = 0
    beat = 1
    name = ""
    dyn = False
    for bar_section in part_data["measures"]:
        for measure in bar_section.elements:
            if measure.classes[0] == DYNAMIC or (measure.classes[0] == TEXTEXPRESSION and
                                                 measure.content == "sotto voce assai"):
                position = get_beat_position(beat_count, beat, measure.beat)
                old_beat = position - get_beat_position(beat_count, beat, 1)
                dyn_mean_weighted += (beats_section + old_beat) * last_dyn
                if measure.classes[0] == TEXTEXPRESSION:
                    name += measure.content
                else:
                    name += measure.value
                dyn = True
                wait = True
            elif measure.classes[0] == TEXTEXPRESSION:
                if measure.content == "dolce" or measure.content == "assai":
                    name += " " + measure.content
                else:
                    name += measure.content + " "
            elif measure.classes[0] == TIMESIGNATURE:
                beat_count = measure.beatCount
                beat = get_number_of_beats(measure.ratioString)
            elif measure.classes[0] == REST:
                beats_section -= get_beat_position(beat_count, beat, measure.duration.quarterLength)
                total_beats -= get_beat_position(beat_count, beat, measure.duration.quarterLength)
                dynamics.append(0)

            if dyn and not wait:
                new_dyn = get_dynamic_numeric(name)
                dynamics.append(new_dyn)
                if (beats_section + old_beat) > 0:
                    dyn_grad += (new_dyn - last_dyn) / (beats_section + old_beat)
                last_dyn = new_dyn
                beats_section = - old_beat  # number of beats that has old dynamic
                name = ""
                dyn = False
            wait = False

        beats_section += beat
        total_beats += beat

    dyn_mean_weighted += beats_section * dynamics[-1] if len(dynamics) != 0 else 0

    part_features.update({
        DYNMEAN: mean(dynamics) if len(dynamics) != 0 else 0,
        DYNMEAN_WEIGHTED: dyn_mean_weighted / total_beats if total_beats != 0 else 0,
        DYNGRAD: dyn_grad / (len(dynamics) - 1) if len(dynamics) > 1 else 0,
        DYNABRUPTNESS: dyn_grad / (total_beats - beats_section) if (total_beats - beats_section) > 0 else 0
    })


def get_dynamic_numeric(value):
    if value in DYNAMIC_VALUES:
        return DYNAMIC_VALUES.get(value)
    else:
        return 0


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
