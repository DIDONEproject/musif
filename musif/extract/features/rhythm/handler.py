from statistics import mean
from typing import List

import numpy as np

from musif.cache import hasattr
from musif.config import ExtractConfiguration
from musif.extract.constants import DATA_PART_ABBREVIATION, GLOBAL_TIME_SIGNATURE
from musif.extract.features.core.constants import (
    DATA_MELODIC_LINES,
    DATA_NOTES,
    DATA_NOTES_AND_RESTS,
    DATA_SOUNDING_MEASURES,
)
from musif.extract.features.prefix import get_part_feature, get_score_feature
from musif.musicxml.tempo import get_number_of_beats

from .constants import *

_COMPONENTS = "_rhythm_components"


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

    rhythm_dot = 0
    rhythm_double_dot = 0
    total_sounding_beats = 0

    # Dotted figures are scanned per melodic line, so notes inside Voice
    # sub-streams count too, and the "shorter following" element must itself
    # be a note of the same line (a rest or barline never completes a figure).
    lines = part_data.get(DATA_MELODIC_LINES)
    if lines is None:
        # custom callers may not run the core module first
        lines = [part_data.get(DATA_NOTES_AND_RESTS, part_data[DATA_NOTES])]
    for line in lines:
        for element, following in zip(line, line[1:]):
            if not hasattr(element, "pitch") or not hasattr(following, "pitch"):
                continue
            if element.duration.dots == 0:
                continue
            try:
                beat_duration = float(element.beatDuration.quarterLength)
                same_beat = (
                    following.beatStr.split()[0] == element.beatStr.split()[0]
                )
            except Exception:
                continue
            if (
                element.duration.quarterLength < beat_duration
                and same_beat
                and following.duration.quarterLength
                < element.duration.quarterLength
            ):
                if element.duration.dots == 2:
                    rhythm_double_dot += 1
                else:
                    rhythm_dot += 1

    for measure_index, measure in enumerate(part_data["measures"]):
        for element in measure.elements:
            if element.classes[0] == "TimeSignature":
                beats = get_number_of_beats(element.ratioString)
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
            # raw components so staves sharing an abbreviation can be summed
            _COMPONENTS: (
                sum(notes_duration),
                total_sounding_beats,
                rhythm_dot,
                rhythm_double_dot,
                sum(nonzero_durations),
                len(nonzero_durations),
            ),
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

    # staves sharing an abbreviation are one logical part: sum components
    part_components = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]
        components = part_components.setdefault(part, [0.0, 0, 0, 0, 0.0, 0])
        for i, value in enumerate(part_features[_COMPONENTS]):
            components[i] += value

        total_notes_duration.extend(
            duration
            for note in part_data[DATA_NOTES]
            if (duration := float(note.duration.quarterLength)) != 0.0
        )

    for part, components in part_components.items():
        (
            duration_sum,
            sounding_beats,
            dots,
            double_dots,
            nonzero_sum,
            nonzero_count,
        ) = components
        average_duration = (
            nonzero_sum / nonzero_count if nonzero_count else "NA"
        )
        rhythm_int = duration_sum / sounding_beats if sounding_beats else "NA"
        dotted = dots / sounding_beats if sounding_beats else "NA"
        double_dotted = double_dots / sounding_beats if sounding_beats else "NA"

        features[get_part_feature(part, AVERAGE_DURATION)] = average_duration
        features[get_part_feature(part, RHYTHMINT)] = rhythm_int
        features[get_part_feature(part, DOTTEDRHYTHM)] = dotted
        features[get_part_feature(part, DOUBLE_DOTTEDRHYTHM)] = double_dotted

        rhythm_intensities.append(rhythm_int)
        dotted_rhythm.append(dotted)
        double_dotted_rhythm.append(double_dotted)

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
