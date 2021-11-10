from typing import List, Tuple

from pandas import DataFrame

from musif.common.sort import sort_dict
from musif.config import Configuration
from musif.extract.common import filter_parts_data, part_matches_filter
from musif.extract.constants import DATA_PART_ABBREVIATION
from musif.extract.features.core.handler import DATA_MEASURES, DATA_NOTES, DATA_SOUNDING_MEASURES
from musif.extract.features.prefix import get_family_prefix, get_part_prefix, get_score_prefix, get_sound_prefix
from musif.extract.features.scoring.constants import FAMILY_ABBREVIATION, NUMBER_OF_FILTERED_PARTS, PART_ABBREVIATION, \
    SOUND_ABBREVIATION
from musif.extract.features.tempo.constants import NUMBER_OF_BEATS, TIME_SIGNATURE, TIME_SIGNATURES, TS_MEASURES
from musif.extract.utils import Get_TimeSignature_periods, calculate_total_number_of_beats
from musif.musicxml import Measure, Note, Part
from musif.musicxml.tempo import get_number_of_beats
from .constants import *


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    if not part_matches_filter(part_data[DATA_PART_ABBREVIATION], cfg.parts_filter):
        return {}
    notes = part_data[DATA_NOTES]
    sounding_measures = part_data[DATA_SOUNDING_MEASURES]
    measures = part_data[DATA_MEASURES]
    time_signature = score_data[TIME_SIGNATURE].split(',')
    time_signatures = score_data[TIME_SIGNATURES]
    measures= score_data[TS_MEASURES]
    
    #for repetitions(?)
    # measures_compressed=[i for j, i in enumerate(measures) if i != measures[j-1]]
    part_features.update({
            NOTES: len(notes),
            SOUNDING_MEASURES: len(sounding_measures),
            MEASURES: len(measures)})

    if len(time_signature) == 1:
            part_features.update({
            SOUNDING_DENSITY: len(notes) / (get_number_of_beats(time_signature[0]) * len(sounding_measures)) if len(sounding_measures) > 0 else 0,
            DENSITY: len(notes) / (get_number_of_beats(time_signature[0]) * len(measures)) if len(measures) > 0 else 0,
        })
    else:
        periods = Get_TimeSignature_periods(time_signatures)
        sounding_measures = range(0, len(sounding_measures)) ## cuando haya repeticiones, revisar esto. Lo hice por un error en la numeracion cuando hay 70x1 (celdillas)
        sounding_time_signatures=[time_signatures[i] for i in sounding_measures]

        sounding_periods = Get_TimeSignature_periods(sounding_time_signatures)
        
        part_features.update({
            SOUNDING_DENSITY: len(notes)/calculate_total_number_of_beats(time_signatures, sounding_periods) if len(sounding_measures) > 0 else 0,
            DENSITY: len(notes)/calculate_total_number_of_beats(time_signatures, periods) if len(measures) > 0 else 0,
        })
        
def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    parts_data = filter_parts_data(parts_data, cfg.parts_filter)
    if len(parts_features) == 0:
        return

    features = {}
    df_parts = DataFrame(parts_features)
    df_sound = df_parts.groupby(SOUND_ABBREVIATION).aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    df_family = df_parts.groupby(FAMILY_ABBREVIATION).aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    df_score = df_parts.aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    number_of_beats = score_features[NUMBER_OF_BEATS]
    for part_features in parts_features:
        part_prefix = get_part_prefix(part_features[PART_ABBREVIATION])
        features[f"{part_prefix}{NOTES}"] = part_features[NOTES]
        features[f"{part_prefix}{SOUNDING_MEASURES}"] = part_features[SOUNDING_MEASURES]
        features[f"{part_prefix}{MEASURES}"] = part_features[MEASURES]
        features[f"{part_prefix}{SOUNDING_DENSITY}"] = part_features[SOUNDING_DENSITY]
        features[f"{part_prefix}{DENSITY}"] = part_features[DENSITY]
        
    for sound_abbreviation in df_sound.index:
        sound_prefix = get_sound_prefix(sound_abbreviation)
        notes = df_sound.loc[sound_abbreviation, NOTES].tolist()
        measures = df_sound.loc[sound_abbreviation, MEASURES].tolist()
        sounding_measures = df_sound.loc[sound_abbreviation, SOUNDING_MEASURES].tolist()
        sound_parts = score_features[f"{sound_prefix}{NUMBER_OF_FILTERED_PARTS}"]
        notes_mean = notes / sound_parts if sound_parts > 0 else 0
        measures_mean = measures / sound_parts if sound_parts > 0 else 0
        sounding_measures_mean = sounding_measures / sound_parts if sound_parts > 0 else 0
        features[f"{sound_prefix}{NOTES}"] = notes
        features[f"{sound_prefix}{NOTES_MEAN}"] = notes_mean
        features[f"{sound_prefix}{SOUNDING_MEASURES}"] = sounding_measures
        features[f"{sound_prefix}{SOUNDING_MEASURES_MEAN}"] = sounding_measures_mean
        features[f"{sound_prefix}{MEASURES}"] = measures
        features[f"{sound_prefix}{MEASURES_MEAN}"] = measures_mean
        features[f"{sound_prefix}{SOUNDING_DENSITY}"] = notes_mean / number_of_beats / sounding_measures_mean if sounding_measures_mean != 0 else 0
        features[f"{sound_prefix}{DENSITY}"] = notes_mean / number_of_beats / measures_mean if measures_mean != 0 else 0
    for family in df_family.index:
        family_prefix = get_family_prefix(family)
        notes = df_family.loc[family, NOTES].tolist()
        measures = df_family.loc[family, MEASURES].tolist()
        sounding_measures = df_family.loc[family, SOUNDING_MEASURES].tolist()
        family_parts = score_features[f"{family_prefix}{NUMBER_OF_FILTERED_PARTS}"]
        notes_mean = notes / family_parts if family_parts > 0 else 0
        measures_mean = measures / family_parts if family_parts > 0 else 0
        sounding_measures_mean = sounding_measures / family_parts if family_parts > 0 else 0
        features[f"{family_prefix}{NOTES}"] = notes
        features[f"{family_prefix}{NOTES_MEAN}"] = notes_mean
        features[f"{family_prefix}{SOUNDING_MEASURES}"] = df_family.loc[family, SOUNDING_MEASURES].tolist()
        features[f"{family_prefix}{SOUNDING_MEASURES_MEAN}"] = sounding_measures_mean
        features[f"{family_prefix}{MEASURES}"] = measures
        features[f"{family_prefix}{MEASURES_MEAN}"] = measures_mean
        features[f"{family_prefix}{SOUNDING_DENSITY}"] = notes_mean / number_of_beats / sounding_measures_mean if sounding_measures_mean != 0 else 0
        features[f"{family_prefix}{DENSITY}"] = notes_mean / number_of_beats / measures_mean if measures_mean != 0 else 0
    score_prefix = get_score_prefix()
    notes = df_score[NOTES].tolist()
    notes_mean = notes / len(parts_data)
    measures = df_score[MEASURES].tolist()
    sounding_measures = df_score[SOUNDING_MEASURES].tolist()
    measures_mean = measures / len(parts_data)
    sounding_measures_mean = sounding_measures / len(parts_data)
    features[f"{score_prefix}{NOTES}"] = notes
    features[f"{score_prefix}{NOTES_MEAN}"] = notes_mean
    features[f"{score_prefix}{SOUNDING_MEASURES}"] = sounding_measures
    features[f"{score_prefix}{SOUNDING_MEASURES_MEAN}"] = sounding_measures_mean
    features[f"{score_prefix}{MEASURES}"] = measures
    features[f"{score_prefix}{MEASURES_MEAN}"] = measures_mean
    features[f"{score_prefix}{SOUNDING_DENSITY}"] = notes_mean / number_of_beats / sounding_measures_mean if sounding_measures_mean != 0 else 0
    features[f"{score_prefix}{DENSITY}"] = notes_mean / number_of_beats / measures_mean if measures_mean != 0 else 0

    score_features.update(features)


def get_notes_and_measures(part: Part) -> Tuple[List[Note], List[Measure], List[Measure]]:
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
        ].duration.quarterLength += subject.duration.quarterLength  # sum tied notes' length across measures


def calculate_densities(notes_list, measures_list, names_list, cfg: Configuration):
    density_list = []
    try:
        for i, part in enumerate(names_list):
            density = round(notes_list[i]/measures_list[i], 3)
            density_list.append({f'{names_list[i]}': density})

        density_dict = dict((key, d[key]) for d in density_list for key in d)
        density_sorting = cfg.scoring_order
        density_dict = sort_dict(density_dict, density_sorting, cfg)
        return density_dict
    except:
        cfg.read_logger.error('Densities problem found: ', exc_info=True)
        return {}
