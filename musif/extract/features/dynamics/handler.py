from statistics import mean
from typing import List

from musif.config import ExtractConfiguration
from musif.extract.features.prefix import get_part_feature, get_score_feature
from musif.logs import pwarn

from musif.extract.features.core.constants import DATA_SOUNDING_MEASURES
from musif.musicxml.tempo import get_number_of_beats, get_quarter_length

from ...constants import DATA_PART_ABBREVIATION, GLOBAL_TIME_SIGNATURE
from .constants import *

_COMPONENTS = "_dynamics_components"


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    # The dynamics of a part are its markings: each one stays in force until
    # the next, through rests as well. A silence is not a dynamic level. (A
    # silent measure used to insert a level of 0, which weighed in the mean
    # as much as a forte or a piano: the mean then followed how often the
    # part fell silent, and winds, which rest a lot, came out "softer" than
    # the strings playing under the same markings.)
    levels = []
    # time since the last marking: real time for the gradient (positions stay
    # coherent), sounding time for the weighted mean. In beats and, for the
    # per-quarter-note twins of the gradient features, in quarter notes.
    beats_section = 0.0
    sounding_section = 0.0
    quarters_section = 0.0
    weighted_sum = 0.0
    weighted_beats = 0.0
    total_beats = 0.0
    total_quarters = 0.0
    dyn_grad = 0.0
    dyn_grad_quarters = 0.0
    transitions = 0
    # None until the first marking: what sounds before it has no stated level
    last_dyn = None
    name = ""
    dyn = False
    global_time_signature = score_data.get(GLOBAL_TIME_SIGNATURE)
    if hasattr(global_time_signature, "ratioString"):
        number_of_beats = get_number_of_beats(global_time_signature.ratioString)
        quarter_length = get_quarter_length(global_time_signature.ratioString)
    else:
        number_of_beats = 1
        quarter_length = 1.0

    def register_level(new_dyn, old_beat, old_quarter, measure_is_sounding):
        nonlocal beats_section, sounding_section, quarters_section
        nonlocal weighted_sum, weighted_beats
        nonlocal dyn_grad, dyn_grad_quarters, transitions, last_dyn
        if last_dyn is not None:
            sounding_gap = sounding_section + (old_beat if measure_is_sounding else 0)
            weighted_sum += sounding_gap * last_dyn
            weighted_beats += sounding_gap
            real_gap = beats_section + old_beat
            real_gap_quarters = quarters_section + old_quarter
            if real_gap > 0 and real_gap_quarters > 0:
                dyn_grad += abs(new_dyn - last_dyn) / real_gap
                dyn_grad_quarters += abs(new_dyn - last_dyn) / real_gap_quarters
                transitions += 1
        levels.append(new_dyn)
        last_dyn = new_dyn
        beats_section = -old_beat
        sounding_section = -(old_beat if measure_is_sounding else 0)
        quarters_section = -old_quarter

    for measure_index, measure in enumerate(part_data["measures"]):
        measure_is_sounding = measure_index in part_data[DATA_SOUNDING_MEASURES]

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
                quarter_length = get_quarter_length(element.ratioString)

            if dyn:
                try:
                    old_beat = float(element.beat) - 1
                except Exception:
                    old_beat = 0.0
                if old_beat != old_beat:  # NaN-safe
                    old_beat = 0.0
                try:
                    old_quarter = float(element.offset)
                except Exception:
                    old_quarter = 0.0
                if old_quarter != old_quarter:
                    old_quarter = 0.0

                if name in ["fp", "pf"]:
                    new_dyn = get_dynamic_numeric(name[0])
                    if new_dyn is not None and new_dyn != last_dyn:
                        register_level(
                            new_dyn, old_beat, old_quarter, measure_is_sounding
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
                    register_level(new_dyn, old_beat, old_quarter, measure_is_sounding)
                name = ""
                dyn = False

        # a pending modifier ("dolce", "sempre"...) never applies beyond its
        # own measure; a stale one used to corrupt the next real dynamic
        name = ""

        total_beats += number_of_beats
        total_quarters += quarter_length
        beats_section += number_of_beats
        quarters_section += quarter_length
        if measure_is_sounding:
            sounding_section += number_of_beats

    if last_dyn is not None:
        weighted_sum += sounding_section * last_dyn
        weighted_beats += sounding_section

    components = (
        list(levels),
        weighted_sum,
        weighted_beats,
        dyn_grad,
        transitions,
        total_beats,
        dyn_grad_quarters,
        total_quarters,
    )
    part_features.update(_dynamics_features(lambda name: name, components))
    # raw components so staves sharing an abbreviation can be pooled
    part_features[_COMPONENTS] = components


def _dynamics_features(make_name, components) -> dict:
    """The dynamics features of one part (or of several staves pooled as one
    part). Without markings there are no dynamics at all (NaN, never 0); a
    single level, or none, leaves the gradient undefined."""
    (
        levels,
        weighted_sum,
        weighted_beats,
        dyn_grad,
        transitions,
        total_beats,
        dyn_grad_quarters,
        total_quarters,
    ) = components
    nan = float("nan")
    return {
        make_name(DYNMEAN): mean(levels) if levels else nan,
        # over the sounding beats that have a marking in force: what sounds
        # before the first marking has no stated level and is left out
        make_name(DYNMEAN_WEIGHTED): float(weighted_sum / weighted_beats)
        if levels and weighted_beats > 0
        else nan,
        make_name(DYNGRAD): float(dyn_grad / transitions) if transitions else nan,
        make_name(DYNABRUPTNESS): float(dyn_grad / total_beats)
        if transitions and total_beats != 0
        else nan,
        make_name(DYNGRAD_QUARTERS): float(dyn_grad_quarters / transitions)
        if transitions
        else nan,
        make_name(DYNABRUPTNESS_QUARTERS): float(dyn_grad_quarters / total_quarters)
        if transitions and total_quarters != 0
        else nan,
    }


_SCORE_MEANS = (
    DYNMEAN,
    DYNMEAN_WEIGHTED,
    DYNGRAD,
    DYNABRUPTNESS,
    DYNGRAD_QUARTERS,
    DYNABRUPTNESS_QUARTERS,
)


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    features = {}

    # staves sharing an abbreviation are one logical part: pool components
    part_components = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]
        pooled = part_components.setdefault(part, [[], 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0])
        for index, value in enumerate(part_features[_COMPONENTS]):
            if index == 0:
                pooled[0].extend(value)
            else:
                pooled[index] += value

    values = {name: [] for name in _SCORE_MEANS}
    for part, pooled in part_components.items():
        pooled_features = _dynamics_features(lambda name: name, pooled)
        for name in _SCORE_MEANS:
            features[get_part_feature(part, name)] = pooled_features[name]
            values[name].append(pooled_features[name])

    # The score values are plain means over the parts that carry markings
    # (parts without any are NaN and stay out; genuine zeros stay in).
    nan = float("nan")
    for name in _SCORE_MEANS:
        defined = _drop_nan(values[name])
        features[get_score_feature(name)] = mean(defined) if defined else nan

    score_features.update(features)


def _drop_nan(values: List[float]) -> List[float]:
    return [v for v in values if v == v]


def get_dynamic_numeric(value):
    if value in DYNAMIC_VALUES:
        return DYNAMIC_VALUES.get(value)
    else:
        pwarn(f"Dynamic value was not identified: {value}; mark ignored")
        return None
