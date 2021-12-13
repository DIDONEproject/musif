from statistics import mean
from typing import List

from musif.extract.constants import DATA_PART_ABBREVIATION

from musif.config import Configuration
from musif.extract.features.prefix import get_score_prefix, get_part_feature, get_score_feature
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
    features = {}

    average_durations = []
    rhythm_intensities = []
    dotted_rhythm = []
    double_dotted_rhythm = []

    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]

        features[get_part_feature(part, AVERAGE_DURATION)] = part_features[AVERAGE_DURATION]
        average_durations.append(part_features[AVERAGE_DURATION])

        features[get_part_feature(part, RHYTHMINT)] = part_features[RHYTHMINT]
        rhythm_intensities.append(part_features[RHYTHMINT])

        features[get_part_feature(part, DOTTEDRHYTHM)] = part_features[DOTTEDRHYTHM]
        dotted_rhythm.append(part_features[DOTTEDRHYTHM])

        features[get_part_feature(part, DOUBLE_DOTTEDRHYTHM)] = part_features[DOUBLE_DOTTEDRHYTHM]
        double_dotted_rhythm.append(part_features[DOUBLE_DOTTEDRHYTHM])

    features.update({
        get_score_feature(AVERAGE_DURATION): mean(average_durations),
        get_score_feature(RHYTHMINT): mean(rhythm_intensities),
        get_score_feature(DOTTEDRHYTHM): mean(dotted_rhythm),
        get_score_feature(DOUBLE_DOTTEDRHYTHM): mean(double_dotted_rhythm)
    })

    score_features.update(features)
