from statistics import mean
from typing import List
from xml.dom.minidom import Element

from musif.config import Configuration
from musif.extract.features.prefix import get_part_feature, get_score_prefix, get_score_feature
from musif.extract.utils import get_beat_position
from musif.musicxml.tempo import get_number_of_beats
from .constants import *
from ...constants import DATA_PART_ABBREVIATION


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    dynamics = []
    beats_section = 0
    dyn_mean_weighted = 0
    total_beats = 0
    total_sounding_beats = 0
    dyn_grad = 0
    last_dyn = 0
    number_of_beats = 1
    name = ""
    old_beat=0
    dyn = False
    first_silence=False

    for bar_section in part_data["measures"]:
        for element in bar_section.elements:
            if element.classes[0] == DYNAMIC or (element.classes[0] == TEXTEXPRESSION and
                                                 element.content == "sotto voce assai"):
                if element.classes[0] == TEXTEXPRESSION:
                    name += element.content
                else:
                    name += element.value
                dyn = True
                wait = True

            elif element.classes[0] == TEXTEXPRESSION:
                if element.content in DYNAMIC_LAST_WORDS:
                    name += " " + element.content
                elif element.content in DYNAMIC_FIRST_WORD:
                    name=element.content + ' '
            elif element.classes[0] == TIMESIGNATURE:
                beats_timesignature = element.beatCount
                number_of_beats = get_number_of_beats(element.ratioString)
            elif element.classes[0] == REST and not first_silence:
                if element.duration.quarterLength >= number_of_beats:
                    first_silence = True
                    new_dyn = 0
                    dynamics.append(new_dyn)
                    position = get_beat_position(beats_timesignature, number_of_beats, element.beat)
                    old_beat = position - get_beat_position(beats_timesignature, number_of_beats, 1)
                    dyn_mean_weighted += (beats_section + old_beat) * last_dyn
                    beats_section, dyn_grad, last_dyn = calculate_gradient(beats_section, dyn_grad, last_dyn, old_beat, new_dyn)
                    name = ""

            if dyn:# and not wait:
                new_dyn = get_dynamic_numeric(name)
                if new_dyn != last_dyn:
                    sub_beat = element.elements[0].beat if element.isStream else element.beat
                    position = get_beat_position(beats_timesignature, number_of_beats,sub_beat )
                    old_beat = position - get_beat_position(beats_timesignature, number_of_beats, 1)
                    dyn_mean_weighted += (beats_section + old_beat) * last_dyn
                    dynamics.append(new_dyn)
                    beats_section, dyn_grad, last_dyn = calculate_gradient(beats_section, dyn_grad, last_dyn, old_beat, new_dyn)
                    name = ""
                    first_silence = False
                dyn = False
            # wait = False

        beats_section += number_of_beats
        total_beats += number_of_beats
        if bar_section in part_data['sounding_measures']: 
            total_sounding_beats += number_of_beats - sum([i.duration.quarterLength for i in bar_section.elements if i.classes[0] == REST]) #all silences in the measure


    dyn_mean_weighted += beats_section * dynamics[-1] if len(dynamics) != 0 else 0


    part_features.update({
        DYNMEAN: mean(dynamics) if len(dynamics) != 0 else 0,
        DYNMEAN_WEIGHTED: dyn_mean_weighted / total_sounding_beats if total_sounding_beats != 0 else 0,
        DYNGRAD: dyn_grad / (len(dynamics) - 1) if len(dynamics) > 1 else 0,
        # DYNABRUPTNESS: dyn_grad / (total_beats - beats_section) if (total_beats - beats_section) > 0 else 0
        DYNABRUPTNESS: dyn_grad / total_sounding_beats if total_sounding_beats != 0 else 0,
    })
    pass
def calculate_gradient(beats_section, dyn_grad, last_dyn, old_beat, new_dyn):
    if (beats_section + old_beat) > 0:
        dyn_grad += abs(new_dyn - last_dyn) / (beats_section + old_beat)
    last_dyn = new_dyn
    beats_section = - old_beat  # number of beats that has old dynamic
    return beats_section, dyn_grad, last_dyn


def get_dynamic_numeric(value):
    if value in DYNAMIC_VALUES:
        return DYNAMIC_VALUES.get(value)
    else:
        return 0


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict],
                         score_features: dict):
    features = {}

    dyn_means = []
    dyn_means_weighted = []
    dyn_grads = []
    dyn_abruptness = []

    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]

        features[get_part_feature(part, DYNMEAN)] = part_features[DYNMEAN]
        dyn_means.append(part_features[DYNMEAN])

        features[get_part_feature(part, DYNMEAN_WEIGHTED)] = part_features[DYNMEAN_WEIGHTED]
        dyn_means_weighted.append(part_features[DYNMEAN_WEIGHTED])

        features[get_part_feature(part, DYNGRAD)] = part_features[DYNGRAD]
        dyn_grads.append(part_features[DYNGRAD])

        features[get_part_feature(part, DYNABRUPTNESS)] = part_features[DYNABRUPTNESS]
        dyn_abruptness.append(part_features[DYNABRUPTNESS])

    #remove zeros from the mean calculation
    dyn_means = [i for i in dyn_means if i != 0.0]
    dyn_means_weighted = [i for i in dyn_means if i != 0.0]
    dyn_grads = [i for i in dyn_means if i != 0.0]
    dyn_abruptness = [i for i in dyn_means if i != 0.0]

    features.update({
        get_score_feature(DYNMEAN): mean(dyn_means) if dyn_means else 0,
        get_score_feature(DYNMEAN_WEIGHTED): mean(dyn_means_weighted) if dyn_means_weighted else 0,
        get_score_feature(DYNGRAD): mean(dyn_grads) if dyn_grads else 0,
        get_score_feature(DYNABRUPTNESS): mean(dyn_abruptness) if dyn_abruptness else 0
    })

    score_features.update(features)
