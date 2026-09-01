from statistics import mean
from typing import List

from musif.config import ExtractConfiguration
from musif.extract.features.prefix import get_part_feature, get_score_feature
from musif.logs import pwarn

from musif.extract.features.core.constants import DATA_SOUNDING_MEASURES
from musif.musicxml.tempo import get_number_of_beats

from ...constants import DATA_PART_ABBREVIATION, GLOBAL_TIME_SIGNATURE
from .constants import *

_COMPONENTS = "_dynamics_components"


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    dynamics = []
    # beats_section counts REAL beats since the last dynamic event (positions
    # stay coherent); sounding_section counts only the sounding ones and feeds
    # the weighted mean, whose denominator is the part's sounding beats.
    beats_section = 0.0
    sounding_section = 0.0
    dyn_mean_weighted = 0.0
    total_beats = 0.0
    total_sounding_beats = 0.0
    dyn_grad = 0.0
    transitions = 0
    # None until the first marking: the jump from silence to the first
    # dynamic is not a transition and must not enter the gradient
    last_dyn = None
    name = ""
    dyn = False
    first_silence = False
    global_time_signature = score_data.get(GLOBAL_TIME_SIGNATURE)
    if hasattr(global_time_signature, "ratioString"):
        number_of_beats = get_number_of_beats(global_time_signature.ratioString)
    else:
        number_of_beats = 1

    def register_level(new_dyn, old_beat, measure_is_sounding):
        nonlocal beats_section, sounding_section, dyn_mean_weighted
        nonlocal dyn_grad, transitions, last_dyn
        sounding_gap = sounding_section + (old_beat if measure_is_sounding else 0)
        real_gap = beats_section + old_beat
        dyn_mean_weighted += sounding_gap * (last_dyn or 0)
        if last_dyn is not None and real_gap > 0:
            dyn_grad += abs(new_dyn - last_dyn) / real_gap
            transitions += 1
        dynamics.append(new_dyn)
        last_dyn = new_dyn
        beats_section = -old_beat
        sounding_section = -(old_beat if measure_is_sounding else 0)

    for measure_index, measure in enumerate(part_data["measures"]):
        measure_is_sounding = measure_index in part_data[DATA_SOUNDING_MEASURES]

        # a fully silent measure resets the prevailing level to 0 (once per
        # stretch of silence). A marking announced inside the silent measure
        # is processed afterwards, so it survives as the new level; and a
        # rest in ONE voice of a sounding measure no longer resets anything.
        if not measure_is_sounding and not first_silence:
            register_level(0, 0, False)
            first_silence = True
            name = ""

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
                number_of_beats = get_number_of_beats(element.ratioString)

            if dyn:
                try:
                    old_beat = float(element.beat) - 1
                except Exception:
                    old_beat = 0.0
                if old_beat != old_beat:  # NaN-safe
                    old_beat = 0.0

                if name in ["fp", "pf"]:
                    new_dyn = get_dynamic_numeric(name[0])
                    if new_dyn is not None and new_dyn != last_dyn:
                        register_level(new_dyn, old_beat, measure_is_sounding)
                        first_silence = False
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
                    register_level(new_dyn, old_beat, measure_is_sounding)
                    first_silence = False
                name = ""
                dyn = False

        # a pending modifier ("dolce", "sempre"...) never applies beyond its
        # own measure; a stale one used to corrupt the next real dynamic
        name = ""

        total_beats += number_of_beats
        beats_section += number_of_beats
        if measure_is_sounding:
            sounding_section += number_of_beats
            total_sounding_beats += number_of_beats

    dyn_mean_weighted += sounding_section * (last_dyn or 0)

    nan = float("nan")
    has_dynamics = len(dynamics) > 0
    part_features.update(
        {
            DYNMEAN: mean(dynamics) if has_dynamics else nan,
            DYNMEAN_WEIGHTED: float(dyn_mean_weighted / total_sounding_beats)
            if has_dynamics and total_sounding_beats != 0
            else nan,
            # no transitions (no markings, or a single one) means the
            # gradient is undefined, never 0
            DYNGRAD: float(dyn_grad / transitions) if transitions else nan,
            DYNABRUPTNESS: float(dyn_grad / total_beats)
            if transitions and total_beats != 0
            else nan,
            # raw components so staves sharing an abbreviation can be pooled
            _COMPONENTS: (
                list(dynamics),
                dyn_mean_weighted,
                total_sounding_beats,
                dyn_grad,
                transitions,
                total_beats,
            ),
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

    # staves sharing an abbreviation are one logical part: pool components
    part_components = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]
        pooled = part_components.setdefault(part, [[], 0.0, 0.0, 0.0, 0, 0.0])
        levels, weighted, sounding, grad, transitions, total = part_features[
            _COMPONENTS
        ]
        pooled[0].extend(levels)
        pooled[1] += weighted
        pooled[2] += sounding
        pooled[3] += grad
        pooled[4] += transitions
        pooled[5] += total

    nan = float("nan")
    for part, pooled in part_components.items():
        levels, weighted, sounding, grad, transitions, total = pooled
        dyn_mean = mean(levels) if levels else nan
        dyn_mean_weighted = (
            weighted / sounding if levels and sounding != 0 else nan
        )
        dyn_grad = grad / transitions if transitions else nan
        abruptness = grad / total if transitions and total != 0 else nan

        features[get_part_feature(part, DYNMEAN)] = dyn_mean
        dyn_means.append(dyn_mean)
        features[get_part_feature(part, DYNMEAN_WEIGHTED)] = dyn_mean_weighted
        dyn_means_weighted.append(dyn_mean_weighted)
        features[get_part_feature(part, DYNGRAD)] = dyn_grad
        dyn_grads.append(dyn_grad)
        features[get_part_feature(part, DYNABRUPTNESS)] = abruptness
        dyn_abruptness.append(abruptness)

    # parts without any marking carry NaN; genuine zeros (a flat part) stay
    dyn_means = _drop_nan(dyn_means)
    dyn_means_weighted = _drop_nan(dyn_means_weighted)
    dyn_grads = _drop_nan(dyn_grads)
    dyn_abruptness = _drop_nan(dyn_abruptness)

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


def get_dynamic_numeric(value):
    if value in DYNAMIC_VALUES:
        return DYNAMIC_VALUES.get(value)
    else:
        pwarn(f"Dynamic value was not identified: {value}; mark ignored")
        return None
