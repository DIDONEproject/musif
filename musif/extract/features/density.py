from typing import List, Tuple

from pandas import DataFrame
from musif.common.sort import sort_dict
from musif.config import Configuration
from musif.extract.common import filter_parts_data, part_matches_filter
from musif.extract.constants import DATA_PARTS_FILTER, DATA_PART_ABBREVIATION
from musif.extract.features.core import DATA_NOTES, DATA_SOUNDING_MEASURES, DATA_MEASURES
from musif.extract.features.tempo import TIME_SIGNATURE, TIME_SIGNATURES, TS_CHANGES, get_number_of_beats
from musif.extract.features.prefix import get_family_prefix, get_part_prefix, get_score_prefix, get_sound_prefix
from musif.extract.features.scoring import NUMBER_OF_FILTERED_PARTS, SOUND_ABBREVIATION, FAMILY_ABBREVIATION, \
    PART_ABBREVIATION
from musif.extract.features.tempo import NUMBER_OF_BEATS
from musif.musicxml import Measure, Note, Part

NOTES = "Notes"
NOTES_MEAN = "NotesMean"
SOUNDING_MEASURES = "SoundingMeasures"
SOUNDING_MEASURES_MEAN = "SoundingMeasuresMean"
MEASURES = "Measures"
MEASURES_MEAN = "MeasuresMean"
SOUNDING_DENSITY = "SoundingDensity"
DENSITY = "Density"

def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    if not part_matches_filter(part_data[DATA_PART_ABBREVIATION], score_data[DATA_PARTS_FILTER]):
        return {}
    notes = part_data[DATA_NOTES]
    sounding_measures = part_data[DATA_SOUNDING_MEASURES]
    measures = part_data[DATA_MEASURES]
    number_of_beats = part_features[NUMBER_OF_BEATS]
    time_signatures = score_data[TIME_SIGNATURES]
    time_signature = score_data[TIME_SIGNATURE]
    time_signatures_changes = score_data[TS_CHANGES]

    part_features.update({
            NOTES: len(notes),
            SOUNDING_MEASURES: len(sounding_measures),
            MEASURES: len(measures)})

    if len(set(time_signatures)) == 1:
            part_features.update({
            SOUNDING_DENSITY: len(notes) / get_number_of_beats(time_signature)  / len(sounding_measures) if len(sounding_measures) > 0 else 0,
            DENSITY: len(notes) / get_number_of_beats(time_signature) / len(measures) if len(measures) > 0 else 0,
        })
    else:
        periods_ts=[]
        time_changes=[]
        # for t in range(1, len(time_signatures)):
            # if time_signatures[t] != time_signatures[t-1]:
            #     # what measure in compressed list corresponds to the change in time signature
            #     time_changes.append(time_signatures[t-1])
            #     periods_ts.append(len(measures_compressed[0:playthrough[t-1]])-sum(periods_ts))

        sounding_density = len(notes)/sum([period * get_number_of_beats(time_signatures_changes[j]) for j, period in enumerate(time_signatures)])
        
        part_features.update({
            # SOUNDING_DENSITY: len(notes) / number_of_beats / len(sounding_measures) if len(sounding_measures) > 0 else 0,
            DENSITY: len(notes) / number_of_beats / len(measures) if len(measures) > 0 else 0,
        })
        pass

def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    parts_data = filter_parts_data(parts_data, score_data[DATA_PARTS_FILTER])
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
