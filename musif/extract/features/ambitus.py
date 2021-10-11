from typing import List

from music21.interval import Interval

from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.constants import DATA_PART, DATA_PARTS_FILTER, DATA_PART_ABBREVIATION
from musif.extract.features.core import DATA_NUMERIC_INTERVALS
from musif.extract.features.prefix import get_part_prefix
from musif.musicxml.ambitus import get_part_ambitus

LOWEST_NOTE = "LowestNote"
HIGHEST_NOTE = "HighestNote"
LOWEST_NOTE_INDEX = "LowestNoteIndex"
HIGHEST_NOTE_INDEX = "HighestNoteIndex"
LARGEST_INTERVAL_ASC = "LargestIntervalAsc"
LARGEST_SEMITONES_ASC = "LargestSemitonesAsc"
LARGEST_ABSOLUTE_SEMITONES_ASC = "LargestAbsoluteSemitonesAsc"
LARGEST_INTERVAL_DESC = "LargestIntervalDesc"
LARGEST_SEMITONES_DESC = "LargestSemitonesDesc"
LARGEST_ABSOLUTE_SEMITONES_DESC = "LargestAbsoluteSemitonesDesc"
LARGEST_INTERVAL_ALL = "LargestIntervalAll"
LARGEST_SEMITONES_ALL = "LargestSemitonesAll"
LARGEST_ABSOLUTE_SEMITONES_ALL = "LargestAbsoluteSemitonesAll"
SMALLEST_INTERVAL_ASC = "SmallestIntervalAsc"
SMALLEST_SEMITONES_ASC = "SmallestSemitonesAsc"
SMALLEST_ABSOLUTE_SEMITONES_ASC = "SmallestAbsoluteSemitonesAsc"
SMALLEST_INTERVAL_DESC = "SmallestIntervalDesc"
SMALLEST_SEMITONES_DESC = "SmallestSemitonesDesc"
SMALLEST_ABSOLUTE_SEMITONES_DESC = "SmallestAbsoluteSemitonesDesc"
SMALLEST_INTERVAL_ALL = "SmallestIntervalAll"
SMALLEST_SEMITONES_ALL = "SmallestSemitonesAll"
SMALLEST_ABSOLUTE_SEMITONES_ALL = "SmallestAbsoluteSemitonesAll"


ALL_FEATURES = [
    LOWEST_NOTE_INDEX, LOWEST_NOTE, HIGHEST_NOTE_INDEX, HIGHEST_NOTE, LARGEST_INTERVAL_ASC, LARGEST_SEMITONES_ASC,
    LARGEST_ABSOLUTE_SEMITONES_ASC, LARGEST_INTERVAL_DESC, LARGEST_SEMITONES_DESC, LARGEST_ABSOLUTE_SEMITONES_DESC,
    LARGEST_INTERVAL_ALL, LARGEST_SEMITONES_ALL, LARGEST_ABSOLUTE_SEMITONES_ALL, SMALLEST_INTERVAL_ASC,
    SMALLEST_SEMITONES_ASC, SMALLEST_ABSOLUTE_SEMITONES_ASC, SMALLEST_INTERVAL_DESC, SMALLEST_SEMITONES_DESC,
    SMALLEST_ABSOLUTE_SEMITONES_DESC, SMALLEST_INTERVAL_ALL, SMALLEST_SEMITONES_ALL, SMALLEST_ABSOLUTE_SEMITONES_ALL
]


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    part = part_data[DATA_PART]
    this_aria_ambitus, ambitus_pitch_span = get_part_ambitus(part)
    lowest_note, highest_note = ambitus_pitch_span
    lowest_note_text = lowest_note.nameWithOctave.replace("-", "b")
    highest_note_text = highest_note.nameWithOctave.replace("-", "b")
    lowest_note_index = int(lowest_note.ps)
    highest_note_index = int(highest_note.ps)
    numeric_intervals = [interval for interval in part_data[DATA_NUMERIC_INTERVALS] if interval != 0]
    ascending_intervals = [interval for interval in numeric_intervals if interval > 0]
    descending_intervals = [interval for interval in numeric_intervals if interval < 0]
    largest_semitones = max(numeric_intervals) if len(numeric_intervals) > 0 else None
    largest = Interval(largest_semitones).directedName if len(numeric_intervals) > 0 else None
    smallest_semitones = sorted(numeric_intervals, key=abs)[0] if len(numeric_intervals) > 0 else None
    smallest = Interval(smallest_semitones).directedName if len(numeric_intervals) > 0 else None
    largest_ascending_semitones = max(ascending_intervals) if len(ascending_intervals) > 0 else None
    largest_ascending = Interval(largest_ascending_semitones).directedName if len(ascending_intervals) > 0 else None
    largest_descending_semitones = min(descending_intervals) if len(descending_intervals) > 0 else None
    largest_descending = Interval(largest_descending_semitones).directedName if len(descending_intervals) > 0 else None
    smallest_ascending_semitones = min(ascending_intervals) if len(ascending_intervals) > 0 else None
    smallest_ascending = Interval(smallest_ascending_semitones).directedName if len(ascending_intervals) > 0 else None
    smallest_descending_semitones = max(descending_intervals) if len(descending_intervals) > 0 else None
    smallest_descending = Interval(smallest_descending_semitones).directedName if len(descending_intervals) > 0 else None

    ambitus_features = {
        LOWEST_NOTE: lowest_note_text,
        HIGHEST_NOTE: highest_note_text,
        LOWEST_NOTE_INDEX: lowest_note_index,
        HIGHEST_NOTE_INDEX: highest_note_index,
        LARGEST_INTERVAL_ALL: largest,
        LARGEST_INTERVAL_ASC: largest_ascending,
        LARGEST_INTERVAL_DESC: largest_descending,
        LARGEST_SEMITONES_ALL: largest_semitones,
        LARGEST_SEMITONES_ASC: largest_ascending_semitones,
        LARGEST_SEMITONES_DESC: largest_descending_semitones,
        LARGEST_ABSOLUTE_SEMITONES_ALL: abs(largest_semitones) if largest_semitones else None,
        LARGEST_ABSOLUTE_SEMITONES_ASC: abs(largest_ascending_semitones) if largest_ascending_semitones else None,
        LARGEST_ABSOLUTE_SEMITONES_DESC: abs(largest_descending_semitones) if largest_descending_semitones else None,
        SMALLEST_INTERVAL_ALL: smallest,
        SMALLEST_INTERVAL_ASC: smallest_ascending,
        SMALLEST_INTERVAL_DESC: smallest_descending,
        SMALLEST_SEMITONES_ALL: smallest_semitones,
        SMALLEST_SEMITONES_ASC: smallest_ascending_semitones,
        SMALLEST_SEMITONES_DESC: smallest_descending_semitones,
        SMALLEST_ABSOLUTE_SEMITONES_ALL: abs(smallest_semitones) if smallest_semitones else None,
        SMALLEST_ABSOLUTE_SEMITONES_ASC: abs(smallest_ascending_semitones) if smallest_ascending_semitones else None,
        SMALLEST_ABSOLUTE_SEMITONES_DESC: abs(smallest_descending_semitones) if smallest_descending_semitones else None,
    }
    part_features.update(ambitus_features)


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    parts_data = filter_parts_data(parts_data, score_data[DATA_PARTS_FILTER])
    if len(parts_data) == 0:
        return

    for part_data, part_features in zip(parts_data, parts_features):
        part_prefix = get_part_prefix(part_data[DATA_PART_ABBREVIATION])
        for feature_name in ALL_FEATURES:
            score_features[f"{part_prefix}{feature_name}"] = part_features[feature_name]
