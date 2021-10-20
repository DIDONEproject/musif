from collections import Counter
from typing import List

from musif.config import Configuration
from musif.extract.constants import DATA_PART
from musif.extract.features.prefix import get_score_prefix
from musif.extract.features.tempo import TIME_SIGNATURE, NUMBER_OF_BEATS
from musif.musicxml.tempo import get_number_of_beats

AVERAGE_DURATION = "AverageDuration"
RHYTHMINT = "RhythmInt"


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    notes_duration = [note.duration.quarterLength for note in part_data["notes"]]
    part = part_data[DATA_PART]
    time_signatures = list(part.getTimeSignatures())

    part_features.update({
        AVERAGE_DURATION: sum(notes_duration) / len(notes_duration),
        RHYTHMINT: len(notes_duration)/part_features[NUMBER_OF_BEATS]
    })
    """if len(Counter(time_signatures)) == 1:
          harmonic_rhythm_beats = get_number_of_beats(time_signatures[0])
      else:
          periods_ts = []
          time_changes = []
          for t in range(1, len(time_signatures)):
              if time_signatures[t] != time_signatures[t - 1]:
                  # what measure in compressed list corresponds to the change in time signature
                  time_changes.append(time_signatures[t - 1])
                  periods_ts.append(len(measures_compressed[0:playthrough[t - 1]]) - sum(periods_ts))
          # Calculating harmonic rythm according to beats periods
          harmonic_rhythm_beats = chords_number / sum(
              [period * get_number_of_beats(time_changes[j]) for j, period in enumerate(periods_ts)])"""


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict],
                         score_features: dict):
    prefix = get_score_prefix()
    average_duration_parts = [part[AVERAGE_DURATION] for part in parts_features]
    rhythm_intensity_parts = [part[RHYTHMINT] for part in parts_features]
    score_features.update(({
        f"{prefix}{AVERAGE_DURATION}": sum(average_duration_parts) / len(parts_features),
        f"{prefix}{RHYTHMINT}": sum(rhythm_intensity_parts) / len(parts_features)
    }))

#Estoy un poco enredada, sé que puede haber varios timeSignature para cada parte pero como el cálculo de nº de notas/ beat, cómo sabría qué notas van con cada timeSignature?