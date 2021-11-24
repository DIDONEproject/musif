from os import path
from typing import List

from musif.config import Configuration
from musif.extract.constants import DATA_FILE, DATA_PART, DATA_SCORE
from musif.extract.features.prefix import part_feature_name, score_feature_name
from musif.musicxml import get_intervals, get_notes_and_measures, get_notes_lyrics
from musif.musicxml.key import get_key_and_mode
from .constants import *


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
        NOTES: len(notes)
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

    for part_data, part_features in zip(parts_data, parts_features):
        score_features[part_feature_name(part_data, NOTES)] = part_features[NOTES]

    score_notes = sum([part_features[NOTES] for part_features in parts_features])
    score_features.update({
        score_feature_name(NOTES): score_notes,
    })
