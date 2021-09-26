from os import path
from typing import List

from musif.config import Configuration
from musif.constants import DATA_PART, DATA_SCORE, DATA_FILE
from musif.musicxml import get_intervals, get_notes_and_measures, get_notes_lyrics
from musif.musicxml.ambitus import get_part_ambitus
from musif.musicxml.key import get_key_and_mode

DATA_NOTES = "notes"
DATA_LYRICS = "lyrics"
DATA_SOUNDING_MEASURES = "sounding_measures"
DATA_MEASURES = "measures"
DATA_NUMERIC_INTERVALS = "numeric_intervals"
DATA_TEXT_INTERVALS = "text_intervals"
DATA_AMBITUS_SOLUTION = "ambitus_solution"
DATA_AMBITUS_PITCH_SPAN = "ambitus_pitch_span"
DATA_KEY = "key"
DATA_TONALITY = "tonality"
DATA_MODE = "mode"

FILE_NAME = "FileName"


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    part = part_data[DATA_PART]
    notes, tied_notes, measures, sounding_measures = get_notes_and_measures(part)
    lyrics = get_notes_lyrics(notes)
    numeric_intervals, text_intervals = get_intervals(notes)
    ambitus_solution, ambitus_pitch_span = get_part_ambitus(part)
    part_data.update({
        DATA_NOTES: tied_notes,
        DATA_LYRICS: lyrics,
        DATA_SOUNDING_MEASURES: sounding_measures,
        DATA_MEASURES: measures,
        DATA_NUMERIC_INTERVALS: numeric_intervals,
        DATA_TEXT_INTERVALS: text_intervals,
        DATA_AMBITUS_SOLUTION: ambitus_solution,
        DATA_AMBITUS_PITCH_SPAN: ambitus_pitch_span,
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
