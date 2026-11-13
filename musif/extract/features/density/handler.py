from typing import List

from musif.config import ExtractConfiguration
from musif.extract.common import _filter_parts_data, _part_matches_filter
from musif.extract.constants import (
    DATA_FAMILY_ABBREVIATION,
    DATA_PART_ABBREVIATION,
    DATA_SOUND_ABBREVIATION,
)
from musif.extract.features.core.handler import (
    DATA_NOTES,
    DATA_SOUNDING_MEASURES,
)
from musif.extract.features.prefix import (
    get_family_feature,
    get_part_feature,
    get_score_feature,
    get_sound_feature,
)
from musif.extract.features.tempo.constants import TIME_SIGNATURES
from musif.extract.utils import _calculate_total_number_of_beats
from musif.musicxml.tempo import get_quarter_length
from .constants import *

_COMPONENTS = "_density_components"


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    if not _part_matches_filter(part_data[DATA_PART_ABBREVIATION], cfg.parts_filter):
        return {}
    notes = part_data[DATA_NOTES]
    sounding_measures = part_data[DATA_SOUNDING_MEASURES]

    time_signatures = part_data[TIME_SIGNATURES]

    sounding_time_signatures = [time_signatures[i] for i in sounding_measures]

    # per-measure sums, so metre changes are respected at EVERY scope. Two
    # units: the beat of each metre, and the quarter note, which is the same
    # in every metre and so makes densities comparable between arias written
    # in 4/4, 2/2 or 3/8
    total_beats = _calculate_total_number_of_beats(time_signatures)
    sounding_beats = _calculate_total_number_of_beats(sounding_time_signatures)
    total_quarters = sum(get_quarter_length(ts) for ts in time_signatures)
    sounding_quarters = sum(get_quarter_length(ts) for ts in sounding_time_signatures)

    # raw components so aggregate scopes (and staves sharing an abbreviation)
    # sum real time instead of assuming one metre
    components = (
        len(notes), total_beats, sounding_beats, total_quarters, sounding_quarters
    )
    part_features.update(_density_features(lambda name: name, components))
    part_features[_COMPONENTS] = components


def _empty_components():
    return [0, 0.0, 0.0, 0.0, 0.0]


def _add(components, addend):
    for index, value in enumerate(addend):
        components[index] += value


def _ratio(numerator, denominator):
    # a part that never sounds has a density of 0 (no notes over the time of
    # the score) but no sounding density: there is no sounding time to divide
    # by, and 0 would read as a part that sounds and plays nothing
    return numerator / denominator if denominator > 0 else float("nan")


def _density_features(make_name, components):
    num_notes, total_beats, sounding_beats, total_quarters, sounding_quarters = (
        components
    )
    return {
        make_name(DENSITY): _ratio(num_notes, total_beats),
        make_name(SOUNDING_DENSITY): _ratio(num_notes, sounding_beats),
        make_name(DENSITY_QUARTERS): _ratio(num_notes, total_quarters),
        make_name(SOUNDING_DENSITY_QUARTERS): _ratio(num_notes, sounding_quarters),
    }


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    parts_data = _filter_parts_data(parts_data, cfg.parts_filter)
    if len(parts_data) == 0:
        return

    features = {}

    part_components = {}
    sound_components = {}
    family_components = {}
    score_components = _empty_components()

    for part_data, part_features in zip(parts_data, parts_features):
        components = part_features.get(_COMPONENTS)
        if components is None:
            continue
        _add(part_components.setdefault(part_data[DATA_PART_ABBREVIATION], _empty_components()), components)
        _add(sound_components.setdefault(part_data[DATA_SOUND_ABBREVIATION], _empty_components()), components)
        _add(family_components.setdefault(part_data[DATA_FAMILY_ABBREVIATION], _empty_components()), components)
        _add(score_components, components)

    for part, components in part_components.items():
        features.update(
            _density_features(lambda n: get_part_feature(part, n), components)
        )
    for sound, components in sound_components.items():
        features.update(
            _density_features(lambda n: get_sound_feature(sound, n), components)
        )
    for family, components in family_components.items():
        features.update(
            _density_features(lambda n: get_family_feature(family, n), components)
        )
    features.update(_density_features(get_score_feature, score_components))

    score_features.update(features)
