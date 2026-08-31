import re
from typing import Dict, List

from musif.config import ExtractConfiguration
from musif.extract.common import _filter_parts_data
from musif.extract.constants import (DATA_MUSESCORE_SCORE,
                                     DATA_PART_ABBREVIATION)
from musif.extract.features.core.constants import DATA_NOTES
from musif.extract.features.prefix import get_part_feature, get_score_feature

from .constants import *
from .utils import get_emphasised_scale_degrees_relative


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    if score_data[DATA_MUSESCORE_SCORE] is not None:
        notes_per_degree_relative = get_emphasised_scale_degrees_relative(
            part_data[DATA_NOTES], score_data, expanded=cfg.expand_repeats
        )
        if notes_per_degree_relative is None: # No harmonic data in the musescore file (or window)
            return

        all_degrees = sum(value for value in notes_per_degree_relative.values())

        for key, value in notes_per_degree_relative.items():
            part_features[DEGREE_RELATIVE_COUNT.format(key=key)] = value
            part_features[DEGREE_RELATIVE_PER.format(key=key)] = (
                value / all_degrees if all_degrees != 0 else 0
            )


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):

    parts_data = _filter_parts_data(parts_data, cfg.parts_filter)

    features = {}

    if len(parts_data) == 0:
        return

    if score_data[DATA_MUSESCORE_SCORE] is None:
        return

    score_notes_per_degree = {}

    for part_data in parts_data:
        notes_per_degree_relative = get_emphasised_scale_degrees_relative(
            part_data[DATA_NOTES], score_data, expanded=cfg.expand_repeats
        )
        if notes_per_degree_relative is None:
            # no harmonic data in the musescore file (or window)
            continue

        for degree, notes in notes_per_degree_relative.items():
            if degree not in score_notes_per_degree:
                score_notes_per_degree[degree] = 0
            score_notes_per_degree[degree] += notes

    all_score_degrees = sum(value for value in score_notes_per_degree.values())

    for degree, value in score_notes_per_degree.items():
        features[get_score_feature(DEGREE_RELATIVE_COUNT.format(key=degree))] = value
        features[get_score_feature(DEGREE_RELATIVE_PER.format(key=degree))] = (
            value / all_score_degrees if all_score_degrees != 0 else 0
        )

    # Promote part-level relative degrees to score scope. Staves sharing an
    # abbreviation are one logical part: counts summed, percentages
    # recomputed (the old copy loop silently kept only the last staff).
    count_pattern = re.compile(DEGREE_RELATIVE_COUNT.format(key="(.+)"))

    part_degree_counts: Dict[str, Dict[str, int]] = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]
        counts = part_degree_counts.setdefault(part, {})
        for feature_name, value in part_features.items():
            match = count_pattern.fullmatch(feature_name)
            if match:
                degree = match.group(1)
                counts[degree] = counts.get(degree, 0) + value

    for part, counts in part_degree_counts.items():
        part_total = sum(counts.values())
        for degree, value in counts.items():
            features[
                get_part_feature(part, DEGREE_RELATIVE_COUNT.format(key=degree))
            ] = value
            features[
                get_part_feature(part, DEGREE_RELATIVE_PER.format(key=degree))
            ] = (value / part_total if part_total != 0 else 0)

    score_features.update(features)
