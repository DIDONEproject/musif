from typing import List

import numpy as np

from musif.config import ExtractConfiguration
from musif.extract.common import _filter_parts_data
from musif.extract.constants import DATA_PART_ABBREVIATION
from musif.extract.features.core.handler import DATA_NOTES
from musif.extract.features.prefix import get_part_prefix
from musif.musicxml.scoring import ROMAN_NUMERALS_FROM_1_TO_20

from .constants import *


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

    # actual note counts per part; staves sharing an abbreviation are summed
    # as one logical part
    notes = {}
    for part_data in parts_data:
        abbreviation = part_data[DATA_PART_ABBREVIATION]
        key = abbreviation[0].upper() + abbreviation[1:]
        notes[key] = notes.get(key, 0) + len(part_data[DATA_NOTES])

    # canonical pair order (the configured scoring order, expanded with the
    # Roman numerals part abbreviations carry), so a given pair always
    # produces the same column name across a corpus, regardless of the order
    # of the staves in each score
    scoring_order = [
        instrument + numeral
        for instrument in getattr(cfg, "scoring_order", []) or []
        for numeral in [""] + ROMAN_NUMERALS_FROM_1_TO_20
    ]

    def _canonical(item):
        name = item[0][0].lower() + item[0][1:]
        try:
            return (0, scoring_order.index(name))
        except ValueError:
            return (1, name)

    ordered = sorted(notes.items(), key=_canonical)

    for i in range(len(ordered)):
        key_1, value_1 = ordered[i]
        for j in range(i + 1, len(ordered)):
            key_2, value_2 = ordered[j]
            if value_2 == 0:
                texture = np.inf if value_1 > 0 else np.nan
            else:
                texture = value_1 / value_2

            part1_prefix = get_part_prefix(key_1).replace("_", "")
            part2_prefix = get_part_prefix(key_2).replace("_", "")
            score_features[f"{part1_prefix}|{part2_prefix}_{TEXTURE}"] = texture


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    pass
