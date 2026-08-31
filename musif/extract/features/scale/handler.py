import re

from typing import Dict, List, Optional, Union


from music21.note import Note


from musif.config import ExtractConfiguration

from musif.extract.common import _filter_parts_data

from musif.extract.features.core.handler import DATA_KEY, DATA_NOTES

from musif.extract.features.prefix import get_part_feature, get_score_feature

from musif.logs import pwarn

from musif.musicxml.common import _get_degrees_and_accidentals

from .constants import *

from ...constants import DATA_PART_ABBREVIATION


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):

    notes = part_data[DATA_NOTES]

    key = score_data[DATA_KEY]

    notes_per_degree = get_notes_per_degree(str(key), notes)

    all_degrees = sum(value for value in notes_per_degree.values())

    for key, value in notes_per_degree.items():

        part_features[DEGREE_COUNT.format(key=key)] = value

        part_features[DEGREE_PER.format(key=key)] = (
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

    if len(parts_data) == 0:
        return

    key = score_data[DATA_KEY]

    score_notes_per_degree = {}

    for part_data in parts_data:

        notes = part_data[DATA_NOTES]

        part_notes_per_degree = get_notes_per_degree(str(key), notes)

        for degree, notes in part_notes_per_degree.items():

            if degree not in score_notes_per_degree:

                score_notes_per_degree[degree] = 0

            score_notes_per_degree[degree] += notes

    all_score_degrees = sum(value for value in score_notes_per_degree.values())

    for key, value in score_notes_per_degree.items():

        score_features[get_score_feature(DEGREE_COUNT.format(key=key))] = value

        score_features[get_score_feature(DEGREE_PER.format(key=key))] = (
            value / all_score_degrees if all_score_degrees != 0 else 0
        )

    # Promote part-level degree features to score scope. Parts sharing an
    # abbreviation are treated as one logical part: their counts are summed
    # and the percentages recomputed from the summed counts.
    degree_count_pattern = re.compile(DEGREE_COUNT.format(key="(.+)"))

    part_degree_counts: Dict[str, Dict[str, int]] = {}

    for part_data, part_features in zip(parts_data, parts_features):

        part = part_data[DATA_PART_ABBREVIATION]

        counts = part_degree_counts.setdefault(part, {})

        for feature_name, value in part_features.items():

            match = degree_count_pattern.fullmatch(feature_name)

            if match:
                degree = match.group(1)
                counts[degree] = counts.get(degree, 0) + value

    for part, counts in part_degree_counts.items():

        part_total = sum(counts.values())

        for degree, value in counts.items():

            score_features[get_part_feature(part, DEGREE_COUNT.format(key=degree))] = value

            score_features[get_part_feature(part, DEGREE_PER.format(key=degree))] = (
                value / part_total if part_total != 0 else 0
            )


def get_notes_per_degree(key: str, notes: List[Note]) -> Dict[str, int]:

    # seed EVERY known accidental so the emitted column set is identical for
    # every score (on-demand keys used to create ragged, file-dependent columns)
    notes_per_degree = {
        to_full_degree(degree, accidental): 0
        for accidental in ACCIDENTAL_ABBREVIATION
        for degree in [1, 2, 3, 4, 5, 6, 7]
    }

    for degree, accidental in _get_degrees_and_accidentals(key, notes):

        full_degree = to_full_degree(degree, accidental)

        if full_degree is None:
            continue

        notes_per_degree[full_degree] = notes_per_degree.get(full_degree, 0) + 1

    return notes_per_degree


def to_full_degree(degree: Union[int, str], accidental: str) -> Optional[str]:

    abbreviation = ACCIDENTAL_ABBREVIATION.get(accidental)

    if abbreviation is None:
        pwarn(f"Unsupported accidental {accidental!r} on degree {degree}; note not counted")
        return None

    return f"{abbreviation}{degree}"
