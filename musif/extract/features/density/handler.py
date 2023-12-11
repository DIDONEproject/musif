from statistics import mean
from typing import List, Tuple

from musif.common.sort import sort_dict
from musif.config import ExtractConfiguration
from musif.extract.common import _filter_parts_data, _part_matches_filter
from musif.extract.constants import (
    DATA_FAMILY_ABBREVIATION,
    DATA_PART_ABBREVIATION,
    DATA_SOUND_ABBREVIATION,
)
from musif.extract.features.core.handler import (
    DATA_MEASURES,
    DATA_NOTES,
    DATA_SOUNDING_MEASURES,
)
from musif.extract.features.prefix import (
    get_family_feature,
    get_family_prefix,
    get_part_feature,
    get_part_prefix,
    get_score_feature,
    get_score_prefix,
    get_sound_feature,
    get_sound_prefix,
)
from musif.extract.basic_modules.scoring.constants import NUMBER_OF_FILTERED_PARTS
from musif.extract.features.tempo.constants import (
    NUMBER_OF_BEATS,
    TIME_SIGNATURE,
    TIME_SIGNATURES,
)
from musif.extract.utils import (
    _calculate_total_number_of_beats,
)
from musif.logs import lerr
from musif.musicxml import Measure, Note, Part
from musif.musicxml.tempo import get_number_of_beats
from .constants import *
from musif.extract.features.core.constants import (
    NUM_MEASURES,
    NUM_NOTES,
    NUM_SOUNDING_MEASURES,
)
from musif.cache import isinstance


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    if not _part_matches_filter(part_data[DATA_PART_ABBREVIATION], cfg.parts_filter):
        return {}
    notes = part_data[DATA_NOTES]
    sounding_measures = part_data[DATA_SOUNDING_MEASURES]

    time_signatures = part_data[TIME_SIGNATURES]

    sounding_time_signatures = [time_signatures[i] for i in sounding_measures]

    part_features.update(
        {
            SOUNDING_DENSITY: len(notes) / _calculate_total_number_of_beats(sounding_time_signatures)
            if len(sounding_time_signatures) > 0
            else 0,
            DENSITY: len(notes)
            / _calculate_total_number_of_beats(time_signatures)
            if len(time_signatures) > 0 else 0,
        }
    )


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):

    parts_data = _filter_parts_data(parts_data, cfg.parts_filter)
    if len(parts_features) == 0:
        return

    time_signature = score_data[TIME_SIGNATURE].split(",")
    number_of_beats = get_number_of_beats(time_signature[0])

    features = {}
    for i, part_data in enumerate(parts_data):
        part_abbreviation = part_data[DATA_PART_ABBREVIATION.lower()]
        feature_name = get_part_feature(part_abbreviation, SOUNDING_DENSITY)

        if feature_name in features:
            features[feature_name] = mean(
                [features[feature_name], parts_features[i][SOUNDING_DENSITY]]
            )
        else:
            features[feature_name] = parts_features[i][SOUNDING_DENSITY]

        feature_name = get_part_feature(part_abbreviation, DENSITY)
        if feature_name in features:
            features[feature_name] = mean(
                [features[feature_name], parts_features[i][DENSITY]]
            )
        else:
            features[feature_name] = parts_features[i][DENSITY]

    sound_abbreviations = {
        part_data[DATA_SOUND_ABBREVIATION] for part_data in parts_data
    }
    for sound in sound_abbreviations:
        num_parts = score_data[get_sound_feature(sound, NUMBER_OF_FILTERED_PARTS)]
        num_measures = score_features[NUM_MEASURES] * num_parts
        num_sounding_measures = score_features[
            get_sound_feature(sound, NUM_SOUNDING_MEASURES)
        ]
        num_notes = score_features[get_sound_feature(sound, NUM_NOTES)]
        features[get_sound_feature(sound, SOUNDING_DENSITY)] = (
            num_notes / number_of_beats / num_sounding_measures
            if num_sounding_measures != 0
            else 0
        )
        features[get_sound_feature(sound, DENSITY)] = (
            num_notes / number_of_beats / num_measures if num_measures != 0 else 0
        )

    family_abbreviations = {
        part_data[DATA_FAMILY_ABBREVIATION] for part_data in parts_data
    }
    for family in family_abbreviations:
        num_parts = score_data[get_family_feature(family, NUMBER_OF_FILTERED_PARTS)]
        num_measures = score_features[NUM_MEASURES] * num_parts
        num_sounding_measures = score_features[
            get_family_feature(family, NUM_SOUNDING_MEASURES)
        ]
        num_notes = score_features[get_family_feature(family, NUM_NOTES)]
        features[get_family_feature(family, SOUNDING_DENSITY)] = (
            num_notes / number_of_beats / num_sounding_measures
            if num_sounding_measures != 0
            else 0
        )
        features[get_family_feature(family, DENSITY)] = (
            num_notes / number_of_beats / num_measures if num_measures != 0 else 0
        )

    num_parts = score_data[get_score_feature(NUMBER_OF_FILTERED_PARTS)]
    num_measures = score_features[NUM_MEASURES] * num_parts
    num_sounding_measures = score_features[get_score_feature(NUM_SOUNDING_MEASURES)]
    num_notes = score_features[get_score_feature(NUM_NOTES)]
    features[get_score_feature(SOUNDING_DENSITY)] = (
        num_notes / number_of_beats / num_sounding_measures
        if num_sounding_measures != 0
        else 0
    )
    features[get_score_feature(DENSITY)] = (
        num_notes / number_of_beats / num_measures if num_measures != 0 else 0
    )

    score_features.update(features)


def get_notes_and_measures(
    part: Part,
) -> Tuple[List[Note], List[Measure], List[Measure]]:
    notes = []
    measures = list(part.measures(0, None))
    sounding_measures = []
    for measure in measures:
        if len(measure.notes) > 0:
            sounding_measures.append(measure)
        for note in measure.notes:
            set_ties(note, notes)
    return notes, sounding_measures, measures


def set_ties(subject, my_notes_list):
    """
    This function converts tied notes into a unique note
    """
    if subject.tie is None:
        my_notes_list.append(subject)
        return
    if subject.tie.type != "stop" and subject.tie.type != "continue":
        my_notes_list.append(subject)
        return
    if isinstance(my_notes_list[-1], Note):
        # sum tied notes' length
        my_notes_list[-1].duration.quarterLength += subject.duration.quarterLength
        return
    back_counter = -1
    while isinstance(my_notes_list[back_counter], tuple):
        back_counter -= -1
    else:
        my_notes_list[
            back_counter
        ].duration.quarterLength += (
            subject.duration.quarterLength
        )  # sum tied notes' length across measures


def calculate_densities(notes_list, measures_list, names_list, cfg: ExtractConfiguration):
    density_list = []
    try:
        for i, part in enumerate(names_list):
            density = round(notes_list[i] / measures_list[i], 3)
            density_list.append({f"{names_list[i]}": density})

        density_dict = dict((key, d[key]) for d in density_list for key in d)
        density_sorting = cfg.scoring_order
        density_dict = sort_dict(density_dict, density_sorting)
        return density_dict
    except:
        lerr("Densities problem found: ", exc_info=True)
        return {}
