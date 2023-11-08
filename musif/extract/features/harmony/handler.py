from typing import List
from musif.extract.features.core.constants import FILE_NAME

from pandas import DataFrame

from musif.config import ExtractConfiguration
from musif.extract.features.core.handler import DATA_MODE
from musif.logs import perr, pwarn
from .constants import *
from .utils import (
    get_additions,
    get_chord_types,
    get_chords,
    get_harmonic_rhythm,
    get_keyareas,
    get_numerals,
)
from ...constants import DATA_MUSESCORE_SCORE


def get_harmony_data(score_features: dict, harmonic_analysis: DataFrame) -> dict:

    harmonic_rhythm = get_harmonic_rhythm(harmonic_analysis)
    numerals = get_numerals(harmonic_analysis)
    chord_types = get_chord_types(harmonic_analysis)
    additions = get_additions(harmonic_analysis)
    return dict(**harmonic_rhythm, **numerals, **chord_types, **additions)


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    features = {}
    try:
        harmonic_analysis = score_data.get(DATA_MUSESCORE_SCORE)

        if harmonic_analysis is None or harmonic_analysis.empty:
            file_name = score_features[FILE_NAME]
            pwarn(f"No harmonic analysis was found in {file_name} or one of its windows.")
            features[HARMONY_AVAILABLE] = 0
            return features
        else:
            features[HARMONY_AVAILABLE] = 1

        all_harmonic_info = get_harmony_data(score_features, harmonic_analysis)
        keyareas = get_keyareas(
            harmonic_analysis, major=score_data[DATA_MODE] == "major"
        )
        chords, chords_grouping1, chords_grouping2 = get_chords(harmonic_analysis)

        features[f"{HARMONIC_RHYTHM}"] = all_harmonic_info[HARMONIC_RHYTHM]
        features[f"{HARMONIC_RHYTHM_BEATS}"] = all_harmonic_info[HARMONIC_RHYTHM_BEATS]
        features.update(
            {
                k: v
                for (k, v) in all_harmonic_info.items()
                if k.startswith(NUMERALS_prefix)
            }
        )
        features.update({k: v for (k, v) in keyareas.items()})
        features.update(
            {
                k: v
                for (k, v) in all_harmonic_info.items()
                if k.startswith(CHORD_TYPES_prefix)
            }
        )
        features.update(
            {k: v for (k, v) in chords.items() if k.startswith(CHORD_prefix)}
        )
        features.update({k: v for (k, v) in chords_grouping1.items()})
        features.update({k: v for (k, v) in chords_grouping2.items()})

        features.update(
            {
                k: v
                for (k, v) in all_harmonic_info.items()
                if k.startswith(ADDITIONS_prefix)
            }
        )

    except Exception as e:
        name = score_features[FILE_NAME]
        perr(f"Harmony problem found: {str(e)} in file {name}")

    finally:
        score_features.update(features)


def update_part_objects(score_data, part_data, cfg, part_features):
    pass
