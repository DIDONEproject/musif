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
from ..core.constants import DATA_NOTES


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
    total_beats = 0
    total_sounding_beats = 0

    for measure in part_data["measures"]:
        for i, element in enumerate(measure.elements):
            if element.classes[0] == "Note":
                number_notes += 1
                notes_dict[element.duration.quarterLength] += 1
                total_number_notes += 1
                pos = get_beat_position(beat_count, beats, element.beat)
                # if pos in positions and element.duration.dots > 0: #has dot
                if element.duration.dots > 0 and element.duration.quarterLength < beat_unit: #has dot
                    if i+1 < len(measure.elements): #check next item
                        if measure.elements[i+1].beatStr.split()[0] == element.beatStr.split()[0]:
                            if measure.elements[i+1].duration.quarterLength < element.duration.quarterLength:

                                rhythm_dot += 1

                    if element.duration.dots == 2:
                        rhythm_double_dot += 1
            elif element.classes[0] == "TimeSignature":
                # rhythm_intensity_separated += number_notes / beat
                rhythm_intensity_period.append(sum([float(i)*j for i, j in Counter(notes_dict).items()]) / total_sounding_beats if total_sounding_beats !=0 else 0)
                number_notes = 0
                beat_count = element.beatCount
                beats = get_number_of_beats(element.ratioString)
                beat_unit=element.beatStrength
                # positions = [get_beat_position(beat_count, beats, i + 1) for i in range(beats)]
        total_beats += beats
        
        if measure in part_data['sounding_measures']: 
            total_sounding_beats += beats

    rhythm_intensity_period.append(sum([j/i if i != 0.0 else 0 for i, j in Counter(notes_dict).items()] ) / total_sounding_beats if total_sounding_beats else 0 )
    notes_duration=[i for i in notes_duration if i != 0.0] # remove notes with duration equal to 0

    part_features.update({
        AVERAGE_DURATION: mean(notes_duration) if len(notes_duration) != 0 else 0,
        RHYTHMINT: sum(rhythm_intensity_period),
        DOTTEDRHYTHM: (rhythm_dot / total_sounding_beats) if total_sounding_beats else 0,
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

    total_notes_duration=[]

    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]

        features[get_part_feature(part, AVERAGE_DURATION)] = part_features[AVERAGE_DURATION]
        total_notes_duration.append([i.duration.quarterLength for i in part_data[DATA_NOTES] if i !=0])

        features[get_part_feature(part, RHYTHMINT)] = part_features[RHYTHMINT]
        # rhythm_intensities.append([1/i.duration.quarterLength for i in part_data[DATA_NOTES] if i !=0])
        rhythm_intensities.append(part_features[RHYTHMINT])

        features[get_part_feature(part, DOTTEDRHYTHM)] = part_features[DOTTEDRHYTHM]
        dotted_rhythm.append(part_features[DOTTEDRHYTHM])

        features[get_part_feature(part, DOUBLE_DOTTEDRHYTHM)] = part_features[DOUBLE_DOTTEDRHYTHM]
        double_dotted_rhythm.append(part_features[DOUBLE_DOTTEDRHYTHM])

    dotted_rhythm = [i for i in dotted_rhythm if i != 0.0]
    
    features.update({
        # get_score_feature(AVERAGE_DURATION): mean(average_durations),
        get_score_feature(AVERAGE_DURATION): mean([note for instrument in total_notes_duration for note in instrument]),
        get_score_feature(RHYTHMINT): mean(rhythm_intensities) if rhythm_intensities else 0.0 ,
        # get_score_feature(RHYTHMINT): mean([rythm for instrument in rhythm_intensities for rythm in instrument])/score_features['Score_SoundingMeasures']*BEATS,
        get_score_feature(DOTTEDRHYTHM): mean(dotted_rhythm) if dotted_rhythm else 0.0,
        get_score_feature(DOUBLE_DOTTEDRHYTHM): mean(double_dotted_rhythm) if double_dotted_rhythm else 0.0
    })

    score_features.update(features)