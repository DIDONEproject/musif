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

    # per-measure beat sums, so metre changes are respected at EVERY scope
    total_beats = _calculate_total_number_of_beats(time_signatures)
    sounding_beats = _calculate_total_number_of_beats(sounding_time_signatures)

    part_features.update(
        {
            SOUNDING_DENSITY: len(notes) / sounding_beats
            if sounding_beats > 0
            else 0,
            DENSITY: len(notes) / total_beats if total_beats > 0 else 0,
            # raw components so aggregate scopes (and staves sharing an
            # abbreviation) sum real beats instead of assuming one metre
            _COMPONENTS: (len(notes), total_beats, sounding_beats),
        }
    )


def _add(components, addend):
    components[0] += addend[0]
    components[1] += addend[1]
    components[2] += addend[2]


def _density_features(make_name, components):
    num_notes, total_beats, sounding_beats = components
    return {
        make_name(DENSITY): num_notes / total_beats if total_beats > 0 else 0,
        make_name(SOUNDING_DENSITY): num_notes / sounding_beats
        if sounding_beats > 0
        else 0,
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
    score_components = [0, 0.0, 0.0]

    for part_data, part_features in zip(parts_data, parts_features):
        components = part_features.get(_COMPONENTS)
        if components is None:
            continue
        _add(part_components.setdefault(part_data[DATA_PART_ABBREVIATION], [0, 0.0, 0.0]), components)
        _add(sound_components.setdefault(part_data[DATA_SOUND_ABBREVIATION], [0, 0.0, 0.0]), components)
        _add(family_components.setdefault(part_data[DATA_FAMILY_ABBREVIATION], [0, 0.0, 0.0]), components)
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
