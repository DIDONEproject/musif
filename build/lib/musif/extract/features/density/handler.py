from typing import List, Tuple

from musif.common.sort import sort_dict
from musif.config import Configuration
from musif.extract.common import filter_parts_data, part_matches_filter
from musif.extract.constants import DATA_FAMILY_ABBREVIATION, DATA_FILTERED_PARTS, DATA_PART_ABBREVIATION, \
    DATA_SOUND_ABBREVIATION
from musif.extract.features.core.handler import DATA_MEASURES, DATA_NOTES, DATA_SOUNDING_MEASURES
from musif.extract.features.prefix import get_family_feature, get_family_prefix, get_part_feature, get_part_prefix, \
    get_score_feature, \
    get_score_prefix, \
    get_sound_feature, \
    get_sound_prefix
from musif.extract.features.scoring.constants import NUMBER_OF_FILTERED_PARTS, PART_ABBREVIATION
from musif.extract.features.tempo.constants import NUMBER_OF_BEATS, TIME_SIGNATURE, TIME_SIGNATURES
from musif.extract.utils import Get_TimeSignature_periods, calculate_total_number_of_beats
from musif.logs import lerr
from musif.musicxml import Measure, Note, Part
from musif.musicxml.tempo import get_number_of_beats
from .constants import *
from ..core.constants import NUM_MEASURES, NUM_NOTES, NUM_SOUNDING_MEASURES


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    if not part_matches_filter(part_data[DATA_PART_ABBREVIATION], cfg.parts_filter):
        return {}
    notes = part_data[DATA_NOTES]
    sounding_measures = part_data[DATA_SOUNDING_MEASURES]
    measures = part_data[DATA_MEASURES]
    time_signature = score_data[TIME_SIGNATURE].split(',')
    time_signatures = score_data[TIME_SIGNATURES]
    # measures = score_data[TS_MEASURES]

    #for repetitions(?)
    # measures_compressed=[i for j, i in enumerate(measures) if i != measures[j-1]]

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

    time_signature = score_data[TIME_SIGNATURE].split(',')
    number_of_beats = get_number_of_beats(time_signature[0])

    features = {}
    for part_features in parts_features:
        part = part_features[PART_ABBREVIATION]
        features[get_part_feature(part, SOUNDING_DENSITY)] = part_features[SOUNDING_DENSITY]
        features[get_part_feature(part, DENSITY)] = part_features[DENSITY]

    sound_abbreviations = {part_data[DATA_SOUND_ABBREVIATION] for part_data in parts_data}
    for sound in sound_abbreviations:
        num_parts = score_features[get_sound_feature(sound, NUMBER_OF_FILTERED_PARTS)]
        num_measures = score_features[NUM_MEASURES] * num_parts
        num_sounding_measures = score_features[get_sound_feature(sound, NUM_SOUNDING_MEASURES)]
        num_notes = score_features[get_sound_feature(sound, NUM_NOTES)]
        features[get_sound_feature(sound, SOUNDING_DENSITY)] = num_notes / number_of_beats / num_sounding_measures if num_sounding_measures != 0 else 0
        features[get_sound_feature(sound, DENSITY)] = num_notes / number_of_beats / num_measures if num_measures != 0 else 0

    family_abbreviations = {part_data[DATA_FAMILY_ABBREVIATION] for part_data in parts_data}
    for family in family_abbreviations:
        num_parts = score_features[get_family_feature(family, NUMBER_OF_FILTERED_PARTS)]
        num_measures = score_features[NUM_MEASURES] * num_parts
        num_sounding_measures = score_features[get_family_feature(family, NUM_SOUNDING_MEASURES)]
        num_notes = score_features[get_family_feature(family, NUM_NOTES)]
        features[get_family_feature(family, SOUNDING_DENSITY)] = num_notes / number_of_beats / num_sounding_measures if num_sounding_measures != 0 else 0
        features[get_family_feature(family, DENSITY)] = num_notes / number_of_beats / num_measures if num_measures != 0 else 0

    num_parts = score_features[get_score_feature(NUMBER_OF_FILTERED_PARTS)]
    num_measures = score_features[NUM_MEASURES] * num_parts
    num_sounding_measures = score_features[get_score_feature(NUM_SOUNDING_MEASURES)]
    num_notes = score_features[get_score_feature(NUM_NOTES)]
    features[get_score_feature(SOUNDING_DENSITY)] = num_notes / number_of_beats / num_sounding_measures if num_sounding_measures != 0 else 0
    features[get_score_feature(DENSITY)] = num_notes / number_of_beats / num_measures if num_measures != 0 else 0

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
        density_dict = sort_dict(density_dict, density_sorting)
        return density_dict
    except:
        lerr('Densities problem found: ', exc_info=True)
        return {}
