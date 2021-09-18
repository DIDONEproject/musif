from os import path
from typing import List

from music21.analysis.discrete import Ambitus

from musif.config import Configuration
from musif.extract.features.key import get_key_and_mode
from musif.musicxml import get_intervals, get_notes_and_measures, get_notes_lyrics


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:

    part = part_data["part"]
    notes, tied_notes, measures, sounding_measures = get_notes_and_measures(part)
    lyrics = get_notes_lyrics(notes)
    numeric_intervals, text_intervals = get_intervals(notes)
    ambitus = Ambitus()
    ambitus_solution = ambitus.getSolution(part)
    ambitus_pitch_span = ambitus.getPitchSpan(part)
    part_data.update({
        "notes": tied_notes,
        "lyrics": lyrics,
        "sounding_measures": sounding_measures,
        "measures": measures,
        "numeric_intervals": numeric_intervals,
        "text_intervals": text_intervals,
        "ambitus_solution": ambitus_solution,
        "ambitus_pitch_span": ambitus_pitch_span,
    })
    return {}

def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    score = score_data["score"]
    score_key, tonality, mode = get_key_and_mode(score)
    score_data.update({
        "FileName": path.basename(score_data["file"]),
        "key": score_key,
        "tonality": tonality,
        "mode": mode,
    })
    return {}
