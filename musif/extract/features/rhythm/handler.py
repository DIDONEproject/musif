from collections import Counter, defaultdict
from itertools import groupby
from statistics import mean
from typing import List

import numpy as np
import pandas as pd

from musif.cache import hasattr
from musif.config import ExtractConfiguration
from musif.extract.constants import DATA_PART_ABBREVIATION, GLOBAL_TIME_SIGNATURE
from musif.extract.features.core.constants import DATA_NOTES
from musif.extract.features.prefix import get_part_feature, get_score_feature
from musif.extract.utils import _get_beat_position
from musif.musicxml.tempo import get_number_of_beats

from .constants import *


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):

    notes_duration = [note.duration.quarterLength for note in part_data["notes"]]
    beats = 1
    beat_unit = 1
    total_number_notes = 0
    number_notes = 0
    notes_dict = defaultdict(int)
    rhythm_intensity_period = []
    rhythm_dot = 0
    rhythm_double_dot = 0
    total_beats = 0
    total_sounding_beats = 0
    beat_count = (
        score_data[GLOBAL_TIME_SIGNATURE].beatCount
        if GLOBAL_TIME_SIGNATURE in score_data
        else 1
    )
    motion_features = get_motion_features(part_data)
    part_features.update(motion_features)

    for measure in part_data["measures"]:
        for i, element in enumerate(measure.elements):
            if element.classes[0] == "Note":
                number_notes += 1
                notes_dict[element.duration.quarterLength] += 1
                total_number_notes += 1
                pos = _get_beat_position(beat_count, beats, element.beat)
                if (
                    element.duration.dots > 0
                    and element.duration.quarterLength < beat_unit
                ):
                    if i + 1 < len(measure.elements):  # check next item
                        if (
                            measure.elements[i + 1].beatStr.split()[0]
                            == element.beatStr.split()[0]
                        ):
                            if (
                                measure.elements[i + 1].duration.quarterLength
                                < element.duration.quarterLength
                            ):

                                rhythm_dot += 1

                    if element.duration.dots == 2:
                        rhythm_double_dot += 1
            elif element.classes[0] == "TimeSignature":
                rhythm_intensity_period.append(
                    sum([float(i) * j for i, j in Counter(notes_dict).items()])
                    / total_sounding_beats
                    if total_sounding_beats != 0
                    else 0
                )
                number_notes = 0
                beat_count = element.beatCount
                beats = get_number_of_beats(element.ratioString)
                beat_unit = element.beatStrength
        total_beats += beats

        if measure in part_data["sounding_measures"]:
            total_sounding_beats += beats

    rhythm_intensity_period.append(
        sum([j / i if i != 0.0 else 0 for i, j in Counter(notes_dict).items()])
        / total_sounding_beats
        if total_sounding_beats
        else 0
    )
    notes_duration = [
        i for i in notes_duration if i != 0.0
    ]  # remove notes with duration equal to 0

    part_features.update(
        {
            AVERAGE_DURATION: mean(notes_duration)
            if len(notes_duration) != 0
            else "NA",
            RHYTHMINT: sum(rhythm_intensity_period),
            DOTTEDRHYTHM: (rhythm_dot / total_sounding_beats)
            if total_sounding_beats
            else "NA",
            DOUBLE_DOTTEDRHYTHM: (rhythm_double_dot / total_beats),
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
    average_durations = []
    rhythm_intensities = []
    dotted_rhythm = []
    double_dotted_rhythm = []

    total_notes_duration = []

    for part_data, part_features in zip(parts_data, parts_features):
        part = part_data[DATA_PART_ABBREVIATION]

        features[get_part_feature(part, AVERAGE_DURATION)] = part_features[
            AVERAGE_DURATION
        ]
        total_notes_duration.append(
            [i.duration.quarterLength for i in part_data[DATA_NOTES] if i != 0]
        )

        features[get_part_feature(part, RHYTHMINT)] = part_features[RHYTHMINT]
        # rhythm_intensities.append([1/i.duration.quarterLength for i in part_data[DATA_NOTES] if i !=0])
        rhythm_intensities.append(part_features[RHYTHMINT])

        features[get_part_feature(part, DOTTEDRHYTHM)] = part_features[DOTTEDRHYTHM]
        dotted_rhythm.append(part_features[DOTTEDRHYTHM])

        features[get_part_feature(part, DOUBLE_DOTTEDRHYTHM)] = part_features[
            DOUBLE_DOTTEDRHYTHM
        ]
        double_dotted_rhythm.append(part_features[DOUBLE_DOTTEDRHYTHM])

        features[get_part_feature(part, SPEED_AVG_ABS)] = part_features[SPEED_AVG_ABS]
        features[get_part_feature(part, ACCELERATION_AVG_ABS)] = part_features[
            ACCELERATION_AVG_ABS
        ]
        features[get_part_feature(part, ASCENDENT_AVERAGE)] = part_features[
            ASCENDENT_AVERAGE
        ]
        features[get_part_feature(part, DESCENDENT_AVERAGE)] = part_features[
            DESCENDENT_AVERAGE
        ]
        features[get_part_feature(part, ASCENDENT_PROPORTION)] = part_features[
            ASCENDENT_PROPORTION
        ]
        features[get_part_feature(part, DESCENDENT_PROPORTION)] = part_features[
            DESCENDENT_PROPORTION
        ]

    dotted_rhythm = [i for i in dotted_rhythm if i not in (0.0, "NA")]
    features.update(
        {
            # get_score_feature(AVERAGE_DURATION): mean(average_durations),
            get_score_feature(AVERAGE_DURATION): np.mean(
                [note for instrument in total_notes_duration for note in instrument]
            ),
            get_score_feature(RHYTHMINT): np.mean(rhythm_intensities)
            if rhythm_intensities
            else 0.0,
            # get_score_feature(RHYTHMINT): mean([rythm for instrument in rhythm_intensities for rythm in instrument])/score_features['Score_SoundingMeasures']*BEATS,
            get_score_feature(DOTTEDRHYTHM): np.mean(dotted_rhythm)
            if dotted_rhythm
            else 0.0,
            get_score_feature(DOUBLE_DOTTEDRHYTHM): np.mean(double_dotted_rhythm)
            if double_dotted_rhythm
            else 0.0,
        }
    )

    score_features.update(features)


def get_motion_features(part_data) -> dict:
    notes_midi = []
    notes_duration = []
    for note in part_data["notes_and_rests"]:
        if hasattr(note, "pitch"):
            notes_midi.append(note.pitch.midi)
            notes_duration.append(note.duration.quarterLength)
    
    notes_midi = np.asarray(notes_midi)
    notes_duration = np.asarray(notes_duration)
    
    if len(notes_midi) == 0:
        return {
            SPEED_AVG_ABS: 0,
            ACCELERATION_AVG_ABS: 0,
            ASCENDENT_AVERAGE: 0,
            DESCENDENT_AVERAGE: 0,
            ASCENDENT_PROPORTION: 0,
            DESCENDENT_PROPORTION: 0,
        }

    step = 0.125
    midis_raw = np.repeat(notes_midi, [i / step for i in notes_duration], axis=0)
    spe_raw = np.diff(midis_raw) / step
    acc_raw = np.diff(spe_raw) / step

    # Absolute means of speed and acceleration
    spe_avg_abs = np.mean(abs(spe_raw))
    acc_avg_abs = np.mean(abs(acc_raw))

    # Rolling mean to smooth the midis by +-1 compasses -- not required for
    # statistics based on means but important for detecting increasing sequences
    # with a tolerance.
    measure = 4
    midis_smo_series = pd.Series(midis_raw)
    midis_smo = [
        np.mean(i.to_list())
        for i in midis_smo_series.rolling(2 * measure + 1, center=True)
    ]

    # midis_smo = np.rollmean(midis_raw, k = 2 * compass + 1, align = "center")

    # spe_smo = np.diff(midis_smo) / step
    # acc_smo = np.diff(spe_smo) / step

    # Prolonged ascent/descent chunks in smoothed midis of the aria (allows for
    # small violations in the form of decrements/increments that do not
    # decrease/increase the rolling mean).

    dife = np.diff(midis_smo)

    asc = [(k, sum(1 for i in g)) for k, g in groupby(dife > 0)]
    dsc = [(k, sum(1 for i in g)) for k, g in groupby(dife < 0)]

    asc = [i for b, i in asc if b]
    dsc = [i for b, i in dsc if b]

    # Average length of ascent/descent chunks of the aria
    asc_avg = mean(asc) if asc else np.nan
    dsc_avg = mean(dsc) if dsc else np.nan

    # Proportion of ascent/descent chunks over the total of the aria
    asc_prp = sum(asc) / (len(dife) - 1) if asc else np.nan
    dsc_prp = sum(dsc) / (len(dife) - 1) if dsc else np.nan

    return {
        SPEED_AVG_ABS: spe_avg_abs,
        ACCELERATION_AVG_ABS: acc_avg_abs,
        ASCENDENT_AVERAGE: asc_avg,
        DESCENDENT_AVERAGE: dsc_avg,
        ASCENDENT_PROPORTION: asc_prp,
        DESCENDENT_PROPORTION: dsc_prp,
    }
