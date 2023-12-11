from os import path
from typing import List
import pandas as pd
from music21 import *
from music21.stream import Measure
from musif.extract.constants import DATA_FILTERED_PARTS
from musif.extract.features.tempo.constants import TIME_SIGNATURE

from musif.config import ExtractConfiguration
from musif.extract.basic_modules.scoring.constants import (
    FAMILY_ABBREVIATION,
    NUMBER_OF_FILTERED_PARTS,
    SOUND_ABBREVIATION,
)
from musif.extract.constants import (
    DATA_FAMILY_ABBREVIATION,
    DATA_FILE,
    DATA_MUSESCORE_SCORE,
    DATA_PART,
    DATA_PART_ABBREVIATION,
    DATA_SCORE,
    DATA_SOUND_ABBREVIATION,
    GLOBAL_TIME_SIGNATURE,
)
from musif.extract.features.prefix import (
    get_family_feature,
    get_part_feature,
    get_score_feature,
    get_sound_feature,
)
from musif.musicxml.common import (
    _get_intervals,
    _get_lyrics_in_notes,
    get_notes_and_measures,
)
from musif.musicxml.key import get_key_and_mode, _get_key_signature, get_name_from_key

from .constants import *


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    part = part_data[DATA_PART]
    (
        notes,
        measures,
        sounding_measures,
        notes_and_rests,
    ) = get_notes_and_measures(part)
    lyrics = _get_lyrics_in_notes(notes)
    intervals = _get_intervals(notes)
    part_data.update(
        {
            DATA_NOTES: notes,
            DATA_LYRICS: lyrics,
            DATA_SOUNDING_MEASURES: sounding_measures,
            DATA_MEASURES: measures,
            DATA_INTERVALS: intervals,
            DATA_NOTES_AND_RESTS: notes_and_rests,
        }
    )
    part_features.update(
        {
            NUM_NOTES: len(notes),
            NUM_MEASURES: len(measures),
            NUM_SOUNDING_MEASURES: len(sounding_measures),
        }
    )


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    score = score_data[DATA_SCORE]
    score_key, key_name, mode = get_key_and_mode(score)
    if (
        cfg.is_requested_musescore_file()
        and (score_data[DATA_MUSESCORE_SCORE] is not None)
        and (not score_data[DATA_MUSESCORE_SCORE].empty)
    ):
        tonality_ms3 = score_data[DATA_MUSESCORE_SCORE].globalkey[0]
        if key_name != tonality_ms3:
            score_key = key.Key(tonality_ms3)
            mode, key_name = get_name_from_key(score_key)

    score_features[FILE_NAME] = path.basename(score_data[DATA_FILE])
    num_measures = len(score.parts[0].getElementsByClass(Measure))
    key_signature = _get_key_signature(score_key)

    part = score.parts[0]
    time_signature = _get_time_signature(score_data)

    score_data.update(
        {
            DATA_KEY: score_key,
            KEY_SIGNATURE: key_signature,
            TIME_SIGNATURE: time_signature,
            KEY_SIGNATURE: key_signature,
            DATA_KEY_NAME: key_name,
            DATA_MODE: mode,
            DATA_MEASURES: num_measures,
        }
    )

    features = {}
    for i, part in enumerate(parts_features):
        part[SOUND_ABBREVIATION] = parts_data[i][DATA_SOUND_ABBREVIATION]
        part[FAMILY_ABBREVIATION] = parts_data[i][DATA_FAMILY_ABBREVIATION]

    df_parts = pd.DataFrame(parts_features)
    df_sound = df_parts.groupby(SOUND_ABBREVIATION).aggregate(
        {NUM_NOTES: "sum", NUM_SOUNDING_MEASURES: "sum"}
    )
    df_family = df_parts.groupby(FAMILY_ABBREVIATION).aggregate(
        {NUM_NOTES: "sum", NUM_SOUNDING_MEASURES: "sum"}
    )
    df_score = df_parts.aggregate({NUM_NOTES: "sum", NUM_SOUNDING_MEASURES: "sum"})

    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]
        features[get_part_feature(part, NUM_NOTES)] = part_features[NUM_NOTES]
        features[get_part_feature(part, NUM_SOUNDING_MEASURES)] = part_features[
            NUM_SOUNDING_MEASURES
        ]
        part_data[get_part_feature(part, NUM_NOTES)] = part_features[NUM_NOTES]
        part_data[get_part_feature(part, NUM_SOUNDING_MEASURES)] = part_features[
            NUM_SOUNDING_MEASURES
        ]

    for sound in df_sound.index:
        notes = df_sound.loc[sound, NUM_NOTES].tolist()
        sounding_measures = df_sound.loc[sound, NUM_SOUNDING_MEASURES].tolist()
        sound_parts = score_data[get_sound_feature(sound, NUMBER_OF_FILTERED_PARTS)]
        notes_mean = notes / sound_parts if sound_parts > 0 else 0
        sounding_measures_mean = (
            sounding_measures / sound_parts if sound_parts > 0 else 0
        )
        features[get_sound_feature(sound, NUM_NOTES)] = notes
        features[get_sound_feature(sound, NOTES_MEAN)] = notes_mean
        features[get_sound_feature(sound, NUM_SOUNDING_MEASURES)] = sounding_measures
        features[
            get_sound_feature(sound, SOUNDING_MEASURES_MEAN)
        ] = sounding_measures_mean

    for family in df_family.index:
        notes = df_family.loc[family, NUM_NOTES].tolist()
        sounding_measures = df_family.loc[family, NUM_SOUNDING_MEASURES].tolist()
        family_parts = score_data[get_family_feature(family, NUMBER_OF_FILTERED_PARTS)]
        notes_mean = notes / family_parts if family_parts > 0 else 0
        sounding_measures_mean = (
            sounding_measures / family_parts if family_parts > 0 else 0
        )
        features[get_family_feature(family, NUM_NOTES)] = notes
        features[get_family_feature(family, NOTES_MEAN)] = notes_mean
        features[get_family_feature(family, NUM_SOUNDING_MEASURES)] = df_family.loc[
            family, NUM_SOUNDING_MEASURES
        ].tolist()
        features[
            get_family_feature(family, SOUNDING_MEASURES_MEAN)
        ] = sounding_measures_mean

    notes = df_score[NUM_NOTES].tolist()
    notes_mean = notes / len(parts_data)
    sounding_measures = df_score[NUM_SOUNDING_MEASURES].tolist()
    sounding_measures_mean = sounding_measures / len(parts_data)
    features[get_score_feature(NUM_NOTES)] = notes
    features[get_score_feature(NOTES_MEAN)] = notes_mean
    features[get_score_feature(NUM_SOUNDING_MEASURES)] = sounding_measures
    features[get_score_feature(SOUNDING_MEASURES_MEAN)] = sounding_measures_mean
    features[NUM_MEASURES] = num_measures
    score_features.update(features)


def _get_time_signature(score_data: dict) -> str:
    """
    This function takes in a dictionary of score data and returns the global time
    signature of the score as a string.

    Parameters:
    score_data (dict): A dictionary containing score data.

    Returns:
    str: A string representing the time signature of the score. It is `'NA'`
        if no time signature is found.
    """
    if hasattr(score_data.get(GLOBAL_TIME_SIGNATURE), 'ratioString'):
        time_signature = score_data[GLOBAL_TIME_SIGNATURE].ratioString
    else:
        first_measure = score_data[DATA_FILTERED_PARTS][0].getElementsByClass(Measure)[
            0
        ]
        if hasattr(first_measure.timeSignature, 'ratioString'):
            time_signature = first_measure.timeSignature.ratioString
        else:
            time_signature = "NA"
    return time_signature
