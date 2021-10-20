from statistics import mean
from typing import List

from musif.config import Configuration
from musif.extract.constants import DATA_PART
from musif.extract.features.prefix import get_score_prefix
from musif.extract.features.tempo import NUMBER_OF_BEATS
from musif.musicxml.tempo import get_number_of_beats

AVERAGE_DURATION = "AverageDuration"
RHYTHMINT = "RhythmInt"  # number of notes / number of beats
RHYTHMINTSEP = "RhythmIntSep"  # SUM number of notes in a time signature/ beat in a time signature


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    notes_duration = [note.duration.quarterLength for note in part_data["notes"]]
    beat = 1
    number_notes = 0
    rhythm_intensity_separated = 0
    for elem in part_data["measures"]:
        for measure in elem.elements:
            if measure.classes[0] == "Note":
                number_notes += 1
            elif measure.classes[0] == "TimeSignature":
                rhythm_intensity_separated += number_notes / beat
                number_notes = 0
                beat = get_number_of_beats(measure.ratioString)

    rhythm_intensity_separated += number_notes / beat

    part_features.update({
        AVERAGE_DURATION: mean(notes_duration),
        RHYTHMINT: len(notes_duration) / part_features[NUMBER_OF_BEATS],
        RHYTHMINTSEP: rhythm_intensity_separated
    })


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict],
                         score_features: dict):
    prefix = get_score_prefix()
    average_duration_parts = [part[AVERAGE_DURATION] for part in parts_features]
    rhythm_intensity_parts = [part[RHYTHMINT] for part in parts_features]
    rhythm_intensity_separated_parts = [part[RHYTHMINTSEP] for part in parts_features]

    score_features.update(({
        f"{prefix}{AVERAGE_DURATION}": mean(average_duration_parts),
        f"{prefix}{RHYTHMINT}": mean(rhythm_intensity_parts),
        f"{prefix}{RHYTHMINTSEP}": mean(rhythm_intensity_separated_parts)
    }))
