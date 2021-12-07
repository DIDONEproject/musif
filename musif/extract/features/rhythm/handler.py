from statistics import mean
from typing import List

from musif.config import Configuration
from musif.extract.features.prefix import get_score_prefix
from musif.extract.utils import get_beat_position
from musif.musicxml.tempo import get_number_of_beats
from .constants import *


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    notes_duration = [note.duration.quarterLength for note in part_data["notes"]]
    beat = 1
    total_number_notes = 0
    number_notes = 0
    rhythm_intensity_separated = 0
    rhythm_dot = 0
    rhythm_double_dot = 0
    positions = []
    total_beats = 0
    for bar_section in part_data["measures"]:
        for measure in bar_section.elements:
            if measure.classes[0] == "Note":
                number_notes += 1
                total_number_notes += 1
                pos = get_beat_position(beat_count, beat, measure.beat)
                if pos in positions and measure.duration.dots > 0:
                    rhythm_dot += 1
                    if measure.duration.dots == 2:
                        rhythm_double_dot += 1
            elif measure.classes[0] == "TimeSignature":
                rhythm_intensity_separated += number_notes / beat
                number_notes = 0
                beat_count = measure.beatCount
                beat = get_number_of_beats(measure.ratioString)
                positions = [get_beat_position(beat_count, beat, i + 1) for i in range(beat)]
        total_beats += beat

    rhythm_intensity_separated += number_notes / beat

    part_features.update({
        AVERAGE_DURATION: mean(notes_duration) if len(notes_duration) != 0 else 0,
        #        RHYTHMINT: total_number_notes / part_features[NUMBER_OF_BEATS],
        RHYTHMINT: rhythm_intensity_separated,
        DOTTEDRHYTHM: (rhythm_dot / total_beats) * 100,
        DOUBLE_DOTTEDRHYTHM: (rhythm_double_dot / total_beats) * 100
    })


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict],
                         score_features: dict):
    prefix = get_score_prefix()
    average_duration_parts = [part[AVERAGE_DURATION] for part in parts_features]

    # rhythm_intensity_parts = [part[RHYTHMINT] for part in parts_features]
    rhythm_intensity_separated_parts = [part[RHYTHMINT] for part in parts_features]
    dic_dotted_rhythm = dict()
    dic_double_dotted_rhythm = dict()
    for part in parts_features:
        dic_dotted_rhythm.update({part["PartAbbreviation"]: part[DOTTEDRHYTHM]})
        dic_double_dotted_rhythm.update({part["PartAbbreviation"]: part[DOUBLE_DOTTEDRHYTHM]})

    score_features.update(({
        f"{prefix}{AVERAGE_DURATION}": mean(average_duration_parts),
        #       f"{prefix}{RHYTHMINT}": mean(rhythm_intensity_parts),
        f"{prefix}{RHYTHMINT}": mean(rhythm_intensity_separated_parts),
        f"{prefix}{DOTTEDRHYTHM}": dic_dotted_rhythm,
        f"{prefix}{DOUBLE_DOTTEDRHYTHM}": dic_double_dotted_rhythm
    }))
