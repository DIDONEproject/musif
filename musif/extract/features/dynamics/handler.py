from copy import deepcopy
from statistics import mean
from typing import List
from xml.dom.minidom import Element

from musif.config import ExtractConfiguration
from musif.extract.features.prefix import get_part_feature, get_score_feature
from musif.extract.utils import _get_beat_position
from musif.logs import lwarn, pwarn

from musif.extract.features.core.constants import DATA_SOUNDING_MEASURES
from musif.musicxml.tempo import get_number_of_beats

from ...constants import DATA_PART_ABBREVIATION
from .constants import *


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    dynamics = []
    beats_section = 0
    dyn_mean_weighted = 0
    total_beats = 0
    total_sounding_beats = 0
    dyn_grad = 0
    last_dyn = 0
    number_of_beats = 1
    name = ""
    old_beat = 0
    dyn = False
    first_silence = False
    beats_timesignature = get_number_of_beats("4/4")

    for measure in part_data["measures"]:
        measure_elements = list(measure.elements)
        for element in measure_elements:
            if (
                element.classes[0] == DYNAMIC
                and not element.value == "sf"
                or (
                    element.classes[0] == TEXTEXPRESSION
                    and element.content == ("sotto voce assai" and "dolce")
                )
            ):
                if element.classes[0] == TEXTEXPRESSION:
                    name += element.content
                else:
                    if element.value in DYNAMIC_FIRST_WORD:
                        name = element.value + name
                    elif name.strip() in DYNAMIC_LAST_WORD:
                        name = element.value + name
                    else:
                        name += element.value
                dyn = True
            elif element.classes[0] == TEXTEXPRESSION:
                if element.content in DYNAMIC_LAST_WORD:
                    name += " " + element.content
                elif element.content in DYNAMIC_FIRST_WORD:
                    name = element.content + " "
            elif element.classes[0] == TIMESIGNATURE:
                beats_timesignature = element.beatCount
                number_of_beats = get_number_of_beats(element.ratioString)
            elif element.classes[0] == REST and not first_silence:
                if element.duration.quarterLength >= number_of_beats:
                    first_silence = True
                    new_dyn = 0
                    dynamics.append(new_dyn)
                    position = _get_beat_position(
                        beats_timesignature, number_of_beats, element.beat
                    )
                    old_beat = position - _get_beat_position(
                        beats_timesignature, number_of_beats, 1
                    )
                    dyn_mean_weighted += (beats_section + old_beat) * last_dyn
                    beats_section, dyn_grad, last_dyn = calculate_gradient(
                        beats_section, dyn_grad, last_dyn, old_beat, new_dyn
                    )
                    name = ""
            if dyn:
                if name in ["fp", "pf"]:
                    new_dyn = get_dynamic_numeric(name[0])
                    if new_dyn != last_dyn:
                        (
                            beats_section,
                            dyn_grad,
                            last_dyn,
                            first_silence,
                            dyn_mean_weighted,
                        ) = calculate_dynamics(
                            dynamics,
                            beats_section,
                            dyn_mean_weighted,
                            dyn_grad,
                            last_dyn,
                            number_of_beats,
                            element,
                            beats_timesignature,
                            new_dyn,
                        )
                    name = name[1]
                if name == "other-dynamics":
                    file_name = score_data["file"]
                    lwarn(
                        f"fsf found in measure {measure.measureNumber} in file {file_name}"
                    )
                    name = "f"

                new_dyn = get_dynamic_numeric(name.strip())
                if new_dyn != last_dyn:
                    (
                        beats_section,
                        dyn_grad,
                        last_dyn,
                        first_silence,
                        dyn_mean_weighted,
                    ) = calculate_dynamics(
                        dynamics,
                        beats_section,
                        dyn_mean_weighted,
                        dyn_grad,
                        last_dyn,
                        number_of_beats,
                        element,
                        beats_timesignature,
                        new_dyn,
                    )
                name = ""
                dyn = False

        beats_section += number_of_beats
        total_beats += number_of_beats
        if measure.measureNumber in part_data[DATA_SOUNDING_MEASURES]:
            total_sounding_beats += number_of_beats

    dyn_mean_weighted += beats_section * dynamics[-1] if len(dynamics) != 0 else 0

    part_features.update(
        {
            DYNMEAN: mean(dynamics) if len(dynamics) != 0 else 0,
            DYNMEAN_WEIGHTED: float(dyn_mean_weighted / total_sounding_beats)
            if total_sounding_beats != 0
            else 0,
            DYNGRAD: float(dyn_grad / (len(dynamics) - 1))
            if (len(dynamics) - 1) > 0
            else 0,
            DYNABRUPTNESS: float(dyn_grad / total_sounding_beats)
            if total_sounding_beats != 0
            else 0,
        }
    )


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    features = {}

    dyn_means = []
    dyn_means_weighted = []
    dyn_grads = []
    dyn_abruptness = []

    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]

        features[get_part_feature(part, DYNMEAN)] = part_features[DYNMEAN]
        dyn_means.append(part_features[DYNMEAN])

        features[get_part_feature(part, DYNMEAN_WEIGHTED)] = part_features[
            DYNMEAN_WEIGHTED
        ]
        dyn_means_weighted.append(part_features[DYNMEAN_WEIGHTED])

        features[get_part_feature(part, DYNGRAD)] = part_features[DYNGRAD]
        dyn_grads.append(part_features[DYNGRAD])

        features[get_part_feature(part, DYNABRUPTNESS)] = part_features[DYNABRUPTNESS]
        dyn_abruptness.append(part_features[DYNABRUPTNESS])

    dyn_means = [i for i in dyn_means if i != 0.0]
    dyn_means_weighted = [i for i in dyn_means_weighted if i != 0.0]
    dyn_grads = [i for i in dyn_grads if i != 0.0]
    dyn_abruptness = [i for i in dyn_abruptness if i != 0.0]

    features.update(
        {
            get_score_feature(DYNMEAN): mean(dyn_means) if dyn_means else 0,
            get_score_feature(DYNMEAN_WEIGHTED): mean(dyn_means_weighted)
            if dyn_means_weighted
            else 0,
            get_score_feature(DYNGRAD): mean(dyn_grads) if dyn_grads else 0,
            get_score_feature(DYNABRUPTNESS): mean(dyn_abruptness)
            if dyn_abruptness
            else 0,
        }
    )

    score_features.update(features)


def calculate_dynamics(
    dynamics,
    beats_section,
    dyn_mean_weighted,
    dyn_grad,
    last_dyn,
    number_of_beats,
    element,
    beats_timesignature,
    new_dyn,
):
    old_beat = calculate_position(number_of_beats, element, beats_timesignature)
    dyn_mean_weighted += (beats_section + old_beat) * last_dyn
    dynamics.append(new_dyn)
    beats_section, dyn_grad, last_dyn = calculate_gradient(
        beats_section, dyn_grad, last_dyn, old_beat, new_dyn
    )
    first_silence = False
    return beats_section, dyn_grad, last_dyn, first_silence, dyn_mean_weighted


def calculate_position(number_of_beats, element, beats_timesignature):
    sub_beat = element.elements[0].beat if element.isStream else element.beat
    position = _get_beat_position(beats_timesignature, number_of_beats, sub_beat)
    old_beat = position - _get_beat_position(beats_timesignature, number_of_beats, 1)
    return old_beat  # - sum([i.duration.quarterLength for i in bar_section.elements if i.classes[0] == REST]) #all silences in the measure


def calculate_gradient(beats_section, dyn_grad, last_dyn, old_beat, new_dyn):
    if (beats_section + old_beat) > 0:
        dyn_grad += abs(new_dyn - last_dyn) / (beats_section + old_beat)
    last_dyn = new_dyn
    beats_section = -old_beat  # number of beats that has old dynamic
    return beats_section, dyn_grad, last_dyn


def get_dynamic_numeric(value):
    if value in DYNAMIC_VALUES:
        return DYNAMIC_VALUES.get(value)
    else:
        pwarn(f"Dynamic value was not identified: {value}")
        return 40  # average value in case of error
