from typing import List, Tuple

from pandas import DataFrame

from musif.common.sort import sort_dict
from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.features.prefix import get_family_prefix, get_part_prefix, get_score_prefix, get_sound_prefix
from musif.extract.features.scoring import NUMBER_OF_PARTS
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


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:
    notes = part_data["notes"]
    sounding_measures = part_data["sounding_measures"]
    measures = part_data["measures"]
    number_of_beats = part_features[NUMBER_OF_BEATS]
    features = {
        NOTES: len(notes),
        SOUNDING_MEASURES: len(sounding_measures),
        MEASURES: len(measures),
        SOUNDING_DENSITY: len(notes) / number_of_beats / len(sounding_measures) if len(sounding_measures) > 0 else 0,
        DENSITY: len(notes) / number_of_beats / len(measures) if len(measures) > 0 else 0,
    }
    return features


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:

    parts_data = filter_parts_data(parts_data, score_data["parts_filter"])
    if len(parts_features) == 0:
        return {}

    features = {}
    df_parts = DataFrame(parts_features)
    df_sound = df_parts.groupby("SoundAbbreviation").aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    df_family = df_parts.groupby("FamilyAbbreviation").aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    df_score = df_parts.aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    number_of_beats = score_features[NUMBER_OF_BEATS]
    for part_features in parts_features:
        part_prefix = get_part_prefix(part_features['PartAbbreviation'])
        features[f"{part_prefix}{NOTES}"] = part_features[NOTES]
        features[f"{part_prefix}{SOUNDING_MEASURES}"] = part_features[SOUNDING_MEASURES]
        features[f"{part_prefix}{MEASURES}"] = part_features[MEASURES]
        features[f"{part_prefix}{SOUNDING_DENSITY}"] = part_features[SOUNDING_DENSITY]
        features[f"{part_prefix}{DENSITY}"] = part_features[DENSITY]
    for sound in df_sound.index:
        sound_prefix = get_sound_prefix(sound)
        notes = df_sound.loc[sound, NOTES].tolist()
        measures = df_sound.loc[sound, MEASURES].tolist()
        sounding_measures = df_sound.loc[sound, SOUNDING_MEASURES].tolist()
        sound_parts = score_features[f"{sound_prefix}{NUMBER_OF_PARTS}"]
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
        family_parts = score_features[f"{family_prefix}{NUMBER_OF_PARTS}"]
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

    return features

def get_corpus_features(
        scores_data: List[dict],
        parts_data: List[dict],
        cfg: Configuration,
        scores_features: List[dict],
        corpus_features: dict
) -> dict:

    features = {}
    # all_parts_data = [part_data for part_data in parts_data]
    # df_parts = DataFrame(parts_features)
    # df_agg_part = df_parts.groupby("Abbreviation").aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    # df_sound = df_parts.groupby("SoundAbbreviation").aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    # df_family = df_parts.groupby("FamilyAbbreviation").aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    # df_score = df_parts.aggregate({NOTES: "sum", MEASURES: "sum", SOUNDING_MEASURES: "sum"})
    # for sound in df_sound.index:
    #     sound_prefix = get_sound_prefix(sound)
    #     features[f"{sound_prefix}{NOTES}"] = df_sound.loc[sound, NOTES].tolist()
    #     features[f"{sound_prefix}{SOUNDING_MEASURES}"] = df_sound.loc[sound, SOUNDING_MEASURES].tolist()
    #     features[f"{sound_prefix}{MEASURES}"] = df_sound.loc[sound, MEASURES].tolist()
    #     features[f"{sound_prefix}{SOUNDING_DENSITY}"] = features[f"{sound_prefix}{NOTES}"] / features[f"{sound_prefix}{SOUNDING_MEASURES}"]
    #     features[f"{sound_prefix}{DENSITY}"] = features[f"{sound_prefix}{NOTES}"] / features[f"{sound_prefix}{MEASURES}"]
    # for sound in df_sound.index:
    #     sound_prefix = get_sound_prefix(sound)
    #     features[f"{sound_prefix}{NOTES}"] = df_sound.loc[sound, NOTES].tolist()
    #     features[f"{sound_prefix}{SOUNDING_MEASURES}"] = df_sound.loc[sound, SOUNDING_MEASURES].tolist()
    #     features[f"{sound_prefix}{MEASURES}"] = df_sound.loc[sound, MEASURES].tolist()
    #     features[f"{sound_prefix}{SOUNDING_DENSITY}"] = features[f"{sound_prefix}{NOTES}"] / features[f"{sound_prefix}{SOUNDING_MEASURES}"]
    #     features[f"{sound_prefix}{DENSITY}"] = features[f"{sound_prefix}{NOTES}"] / features[f"{sound_prefix}{MEASURES}"]
    # for family in df_family.index:
    #     family_prefix = get_family_prefix(family)
    #     features[f"{family_prefix}{NOTES}"] = df_family.loc[family, NOTES].tolist()
    #     features[f"{family_prefix}{SOUNDING_MEASURES}"] = df_family.loc[family, SOUNDING_MEASURES].tolist()
    #     features[f"{family_prefix}{MEASURES}"] = df_family.loc[family, MEASURES].tolist()
    #     features[f"{family_prefix}{SOUNDING_DENSITY}"] = features[f"{family_prefix}{NOTES}"] / features[f"{family_prefix}{SOUNDING_MEASURES}"]
    #     features[f"{family_prefix}{DENSITY}"] = features[f"{family_prefix}{NOTES}"] / features[f"{family_prefix}{MEASURES}"]
    # score_prefix = get_score_prefix()
    # features[f"{score_prefix}{NOTES}"] = df_score[NOTES].tolist()
    # features[f"{score_prefix}{SOUNDING_MEASURES}"] = df_score[SOUNDING_MEASURES].tolist()
    # features[f"{score_prefix}{MEASURES}"] = df_score[MEASURES].tolist()
    # features[f"{score_prefix}{SOUNDING_DENSITY}"] = features[f"{score_prefix}{NOTES}"] / features[f"{score_prefix}{SOUNDING_MEASURES}"]
    # features[f"{score_prefix}{DENSITY}"] = features[f"{score_prefix}{NOTES}"] / features[f"{score_prefix}{MEASURES}"]

    return features


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
