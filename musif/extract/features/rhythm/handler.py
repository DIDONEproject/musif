from collections import Counter, defaultdict
from statistics import mean
from typing import List

from musif.config import Configuration
from musif.extract.constants import DATA_PART_ABBREVIATION
from musif.extract.features.prefix import (get_part_feature, get_score_feature,
                                           get_score_prefix)
from musif.extract.utils import get_beat_position
from musif.musicxml.tempo import get_number_of_beats

from .constants import *


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    
    notes_duration = [note.duration.quarterLength for note in part_data["notes"]]
    beats = 1
    beat_unit=1
    total_number_notes = 0
    number_notes = 0
    notes_dict= defaultdict(int)
    rhythm_intensity_period = []
    rhythm_dot = 0
    rhythm_double_dot = 0
    positions = []
    total_beats = 0
    total_sounding_beats = 0

    for bar_section in part_data["measures"]:
        for element in bar_section.elements:
            if element.classes[0] == "Note":
                number_notes += 1
                notes_dict[element.duration.quarterLength] += 1
                total_number_notes += 1
                pos = get_beat_position(beat_count, beats, element.beat)
                # if pos in positions and element.duration.dots > 0: #has dot
                if element.duration.dots > 0 and element.duration.quarterLength < beat_unit: #has dot
                    rhythm_dot += 1
                    if element.duration.dots == 2:
                        rhythm_double_dot += 1
            elif element.classes[0] == "TimeSignature":
                # rhythm_intensity_separated += number_notes / beat
                rhythm_intensity_period.append(sum([i*j for i, j in Counter(notes_dict)]) / total_sounding_beats if total_sounding_beats !=0 else 0)
                number_notes = 0
                beat_count = element.beatCount
                beats = get_number_of_beats(element.ratioString)
                beat_unit=element.beatStrength
                positions = [get_beat_position(beat_count, beats, i + 1) for i in range(beats)]
        total_beats += beats
        
        if bar_section in part_data['sounding_measures']: 
            total_sounding_beats += beats

    rhythm_intensity_period.append(sum([j/i if i != 0.0 else 0 for i, j in Counter(notes_dict).items()] ) / total_sounding_beats)
    notes_duration=[i for i in notes_duration if i != 0.0] # remove notes with duration equal to 0

    part_features.update({
        AVERAGE_DURATION: mean(notes_duration) if len(notes_duration) != 0 else 0,
        RHYTHMINT: sum(rhythm_intensity_period),
        DOTTEDRHYTHM: (rhythm_dot / total_sounding_beats),
        DOUBLE_DOTTEDRHYTHM: (rhythm_double_dot / total_beats)
    })
pass

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
