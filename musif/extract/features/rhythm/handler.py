from statistics import mean
from typing import List

import numpy as np

from musif.config import ExtractConfiguration
from musif.extract.constants import DATA_PART_ABBREVIATION, GLOBAL_TIME_SIGNATURE
from musif.extract.features.core.constants import DATA_NOTES, DATA_SOUNDING_MEASURES
from musif.extract.features.prefix import get_part_feature, get_score_feature
from musif.musicxml.tempo import get_number_of_beats

from .constants import *


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    notes_duration = [
        float(note.duration.quarterLength) for note in part_data["notes"]
    ]

    global_time_signature = score_data.get(GLOBAL_TIME_SIGNATURE)
    beats = (
        get_number_of_beats(global_time_signature.ratioString)
        if hasattr(global_time_signature, "ratioString")
        else 1
    )
    beat_unit = (
        float(global_time_signature.beatDuration.quarterLength)
        if hasattr(global_time_signature, "beatDuration")
        else 1.0
    )
    rhythm_dot = 0
    rhythm_double_dot = 0
    total_beats = 0
    total_sounding_beats = 0

    for measure_index, measure in enumerate(part_data["measures"]):
        for i, element in enumerate(measure.elements):
            if element.classes[0] == "Note":
                # a dotted figure: a dotted note shorter than one beat,
                # followed on the same beat by a shorter note
                if (
                    element.duration.dots > 0
                    and element.duration.quarterLength < beat_unit
                    and i + 1 < len(measure.elements)
                    and measure.elements[i + 1].beatStr.split()[0]
                    == element.beatStr.split()[0]
                    and measure.elements[i + 1].duration.quarterLength
                    < element.duration.quarterLength
                ):
                    if element.duration.dots == 2:
                        rhythm_double_dot += 1
                    else:
                        rhythm_dot += 1
            elif element.classes[0] == "TimeSignature":
                beats = get_number_of_beats(element.ratioString)
                beat_unit = float(element.beatDuration.quarterLength)
        total_beats += beats

        # DATA_SOUNDING_MEASURES holds 0-based measure indices
        if measure_index in part_data[DATA_SOUNDING_MEASURES]:
            total_sounding_beats += beats

    nonzero_durations = [d for d in notes_duration if d != 0.0]

    part_features.update(
        {
            AVERAGE_DURATION: mean(nonzero_durations)
            if len(nonzero_durations) != 0
            else "NA",
            # Sum of note durations over the beats of the sounding measures
            RHYTHMINT: sum(notes_duration) / total_sounding_beats
            if total_sounding_beats
            else "NA",
            DOTTEDRHYTHM: (rhythm_dot / total_sounding_beats)
            if total_sounding_beats
            else "NA",
            DOUBLE_DOTTEDRHYTHM: (rhythm_double_dot / total_sounding_beats)
            if total_sounding_beats
            else "NA",
        }
    )


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    features = {}
    rhythm_intensities = []
    dotted_rhythm = []
    double_dotted_rhythm = []
    total_notes_duration = []

    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]

        features[get_part_feature(part, AVERAGE_DURATION)] = part_features[
            AVERAGE_DURATION
        ]
        total_notes_duration.extend(
            duration
            for note in part_data[DATA_NOTES]
            if (duration := float(note.duration.quarterLength)) != 0.0
        )

        features[get_part_feature(part, RHYTHMINT)] = part_features[RHYTHMINT]
        rhythm_intensities.append(part_features[RHYTHMINT])

        features[get_part_feature(part, DOTTEDRHYTHM)] = part_features[DOTTEDRHYTHM]
        dotted_rhythm.append(part_features[DOTTEDRHYTHM])

        features[get_part_feature(part, DOUBLE_DOTTEDRHYTHM)] = part_features[
            DOUBLE_DOTTEDRHYTHM
        ]
        double_dotted_rhythm.append(part_features[DOUBLE_DOTTEDRHYTHM])

    # keep genuine zeros; drop only the NA sentinel of silent parts
    rhythm_intensities = [i for i in rhythm_intensities if i != "NA"]
    dotted_rhythm = [i for i in dotted_rhythm if i != "NA"]
    double_dotted_rhythm = [i for i in double_dotted_rhythm if i != "NA"]

    features.update(
        {
            get_score_feature(AVERAGE_DURATION): mean(total_notes_duration)
            if total_notes_duration
            else "NA",
            get_score_feature(RHYTHMINT): np.mean(rhythm_intensities)
            if rhythm_intensities
            else "NA",
            get_score_feature(DOTTEDRHYTHM): np.mean(dotted_rhythm)
            if dotted_rhythm
            else "NA",
            get_score_feature(DOUBLE_DOTTEDRHYTHM): np.mean(double_dotted_rhythm)
            if double_dotted_rhythm
            else "NA",
        }
    )

    score_features.update(features)
