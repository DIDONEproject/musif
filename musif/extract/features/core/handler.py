from os import path
from typing import List

import pandas as pd

from musif.config import Configuration
from musif.extract.constants import DATA_FILE, DATA_PART, DATA_SCORE
from musif.extract.features.prefix import get_family_prefix, get_score_prefix, get_sound_prefix
from musif.musicxml import get_intervals, get_notes_and_measures, get_notes_lyrics
from musif.musicxml.key import get_key_and_mode
from .constants import *
from ..scoring.constants import FAMILY_ABBREVIATION, NUMBER_OF_FILTERED_PARTS, SOUND_ABBREVIATION


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    part = part_data[DATA_PART]
    notes, tied_notes, measures, sounding_measures = get_notes_and_measures(part)
    lyrics = get_notes_lyrics(notes)
    intervals = get_intervals(notes)
    part_data.update({
        DATA_NOTES: notes,
        DATA_LYRICS: lyrics,
        DATA_SOUNDING_MEASURES: sounding_measures,
        DATA_MEASURES: measures,
        DATA_INTERVALS: intervals,
    })
    part_features.update({
        NUM_NOTES: len(notes),
        NUM_MEASURES: len(measures),
        NUM_SOUNDING_MEASURES: len(sounding_measures),
    })


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    score = score_data[DATA_SCORE]
    score_key, tonality, mode = get_key_and_mode(score)
    score_features[FILE_NAME] = path.basename(score_data[DATA_FILE])
    score_data.update({
        DATA_KEY: score_key,
        DATA_TONALITY: tonality,
        DATA_MODE: mode,
    })

    features = {}
    df_parts = pd.DataFrame(parts_features)
    df_sound = df_parts.groupby(SOUND_ABBREVIATION).aggregate({NUM_NOTES: "sum", NUM_MEASURES: "sum", NUM_SOUNDING_MEASURES: "sum"})
    df_family = df_parts.groupby(FAMILY_ABBREVIATION).aggregate({NUM_NOTES: "sum", NUM_MEASURES: "sum", NUM_SOUNDING_MEASURES: "sum"})
    df_score = df_parts.aggregate({NUM_NOTES: "sum", NUM_MEASURES: "sum", NUM_SOUNDING_MEASURES: "sum"})

    for sound_abbreviation in df_sound.index:
        sound_prefix = get_sound_prefix(sound_abbreviation)
        notes = df_sound.loc[sound_abbreviation, NUM_NOTES].tolist()
        num_measures = df_sound.loc[sound_abbreviation, NUM_MEASURES].tolist()
        sounding_measures = df_sound.loc[sound_abbreviation, NUM_SOUNDING_MEASURES].tolist()
        sound_parts = score_features[f"{sound_prefix}{NUMBER_OF_FILTERED_PARTS}"]
        notes_mean = notes / sound_parts if sound_parts > 0 else 0
        sounding_measures_mean = sounding_measures / sound_parts if sound_parts > 0 else 0
        features[f"{sound_prefix}{NUM_NOTES}"] = notes
        features[f"{sound_prefix}{NOTES_MEAN}"] = notes_mean
        features[f"{sound_prefix}{NUM_SOUNDING_MEASURES}"] = sounding_measures
        features[f"{sound_prefix}{SOUNDING_MEASURES_MEAN}"] = sounding_measures_mean
        features[f"{sound_prefix}{NUM_MEASURES}"] = num_measures

    for family in df_family.index:
        family_prefix = get_family_prefix(family)
        notes = df_family.loc[family, NUM_NOTES].tolist()
        num_measures = df_family.loc[family, NUM_MEASURES].tolist()
        sounding_measures = df_family.loc[family, NUM_SOUNDING_MEASURES].tolist()
        family_parts = score_features[f"{family_prefix}{NUMBER_OF_FILTERED_PARTS}"]
        notes_mean = notes / family_parts if family_parts > 0 else 0
        sounding_measures_mean = sounding_measures / family_parts if family_parts > 0 else 0
        features[f"{family_prefix}{NUM_NOTES}"] = notes
        features[f"{family_prefix}{NOTES_MEAN}"] = notes_mean
        features[f"{family_prefix}{NUM_SOUNDING_MEASURES}"] = df_family.loc[family, NUM_SOUNDING_MEASURES].tolist()
        features[f"{family_prefix}{SOUNDING_MEASURES_MEAN}"] = sounding_measures_mean
        features[f"{family_prefix}{NUM_MEASURES}"] = num_measures

    score_prefix = get_score_prefix()
    notes = df_score[NUM_NOTES].tolist()
    notes_mean = notes / len(parts_data)
    num_measures = df_score[NUM_MEASURES].tolist()
    sounding_measures = df_score[NUM_SOUNDING_MEASURES].tolist()
    sounding_measures_mean = sounding_measures / len(parts_data)
    features[f"{score_prefix}{NUM_NOTES}"] = notes
    features[f"{score_prefix}{NOTES_MEAN}"] = notes_mean
    features[f"{score_prefix}{NUM_SOUNDING_MEASURES}"] = sounding_measures
    features[f"{score_prefix}{SOUNDING_MEASURES_MEAN}"] = sounding_measures_mean
    features[f"{score_prefix}{NUM_MEASURES}"] = num_measures

    score_features.update(features)
