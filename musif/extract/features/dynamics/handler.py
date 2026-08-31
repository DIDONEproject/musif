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

from ...constants import DATA_PART_ABBREVIATION, GLOBAL_TIME_SIGNATURE
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
    # None until the first marking: the jump from silence to the first
    # dynamic is not a transition and must not enter the gradient
    last_dyn = None
    name = ""
    old_beat = 0
    dyn = False
    first_silence = False
    global_time_signature = score_data.get(GLOBAL_TIME_SIGNATURE)
    if hasattr(global_time_signature, "ratioString"):
        number_of_beats = get_number_of_beats(global_time_signature.ratioString)
        beats_timesignature = global_time_signature.beatCount
    else:
        number_of_beats = 1
        beats_timesignature = get_number_of_beats("4/4")

    for measure_index, measure in enumerate(part_data["measures"]):
        # inspect the contents of Voice sub-streams too
        measure_elements = []
        for element in measure.elements:
            if element.classes[0] == "Voice":
                measure_elements.extend(element.elements)
            else:
                measure_elements.append(element)
        for element in measure_elements:
            if (
                element.classes[0] == DYNAMIC
                and not element.value == "sf"
                or (
                    element.classes[0] == TEXTEXPRESSION
                    and element.content in ("sotto voce assai", "dolce")
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
                # a rest spanning the whole measure resets the level to 0
                if element.duration.quarterLength >= measure.barDuration.quarterLength:
                    first_silence = True
                    new_dyn = 0
                    dynamics.append(new_dyn)
                    position = _get_beat_position(
                        beats_timesignature, number_of_beats, element.beat
                    )
                    old_beat = position - _get_beat_position(
                        beats_timesignature, number_of_beats, 1
                    )
                    dyn_mean_weighted += (beats_section + old_beat) * (last_dyn or 0)
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
                    # music21 collapses any <other-dynamics> mark to this
                    # literal, so the original text is unrecoverable: skip the
                    # mark instead of guessing a level
                    file_name = score_data["file"]
                    pwarn(
                        f"Unrecognized dynamic mark (<other-dynamics>) in measure "
                        f"{measure.measureNumber} of {file_name}; mark ignored"
                    )
                    name = ""
                    dyn = False
                    continue

                new_dyn = get_dynamic_numeric(name.strip())
                if new_dyn is not None and new_dyn != last_dyn:
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

        # a pending modifier ("dolce", "sempre"...) never applies beyond its
        # own measure; a stale one used to corrupt the next real dynamic
        name = ""

        total_beats += number_of_beats
        # DATA_SOUNDING_MEASURES holds 0-based indices; weighted time advances
        # over the same (sounding) measure set as its denominator
        if measure_index in part_data[DATA_SOUNDING_MEASURES]:
            beats_section += number_of_beats
            total_sounding_beats += number_of_beats

    dyn_mean_weighted += beats_section * dynamics[-1] if len(dynamics) != 0 else 0

    nan = float("nan")
    has_dynamics = len(dynamics) > 0
    part_features.update(
        {
            DYNMEAN: mean(dynamics) if has_dynamics else nan,
            DYNMEAN_WEIGHTED: float(dyn_mean_weighted / total_sounding_beats)
            if has_dynamics and total_sounding_beats != 0
            else nan,
            DYNGRAD: float(dyn_grad / (len(dynamics) - 1))
            if len(dynamics) > 1
            else (0.0 if has_dynamics else nan),
            DYNABRUPTNESS: float(dyn_grad / total_beats)
            if has_dynamics and total_beats != 0
            else nan,
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

    # parts without any marking carry NaN; genuine zeros (a flat part) stay
    dyn_means = _drop_nan(dyn_means)
    dyn_means_weighted = _drop_nan(dyn_means_weighted)
    dyn_grads = _drop_nan(dyn_grads)
    dyn_abruptness = _drop_nan(dyn_abruptness)

    nan = float("nan")
    features.update(
        {
            get_score_feature(DYNMEAN): mean(dyn_means) if dyn_means else nan,
            get_score_feature(DYNMEAN_WEIGHTED): mean(dyn_means_weighted)
            if dyn_means_weighted
            else nan,
            get_score_feature(DYNGRAD): mean(dyn_grads) if dyn_grads else nan,
            get_score_feature(DYNABRUPTNESS): mean(dyn_abruptness)
            if dyn_abruptness
            else nan,
        }
    )

    score_features.update(features)


def _drop_nan(values: List[float]) -> List[float]:
    return [v for v in values if v == v]


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
    dyn_mean_weighted += (beats_section + old_beat) * (last_dyn or 0)
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
    # last_dyn is None before the first marking: silence -> first marking is
    # not a dynamic transition
    if last_dyn is not None and (beats_section + old_beat) > 0:
        dyn_grad += abs(new_dyn - last_dyn) / (beats_section + old_beat)
    last_dyn = new_dyn
    beats_section = -old_beat  # number of beats that has old dynamic
    return beats_section, dyn_grad, last_dyn


def get_dynamic_numeric(value):
    if value in DYNAMIC_VALUES:
        return DYNAMIC_VALUES.get(value)
    else:
        pwarn(f"Dynamic value was not identified: {value}; mark ignored")
        return None
