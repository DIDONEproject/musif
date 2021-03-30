from typing import List

from musif.config import Configuration

LOWEST_NOTE = "LowestNote"
HIGHEST_NOTE = "HighestNote"
LOWEST_INDEX = "LowestIndex"
HIGHEST_INDEX = "HighestIndex"
LOWEST_MEAN_NOTE = "LowestMeanNote"
LOWEST_MEAN_INDEX = "LowestMeanIndex"
HIGHEST_MEAN_NOTE = "HighestMeanNote"
HIGHEST_MEAN_INDEX = "HighestMeanIndex"
AMBITUS_LARGEST_INTERVAL = "AmbitusLargestInterval"
AMBITUS_LARGEST_SEMITONES = "AmbitusLargestSemitones"
AMBITUS_SMALLEST_INTERVAL = "AmbitusSmallestInterval"
AMBITUS_SMALLEST_SEMITONES = "AmbitusSmallestSemitones"
AMBITUS_ABSOLUTE_INTERVAL = "AmbitusAbsoluteInterval"
AMBITUS_ABSOLUTE_SEMITONES = "AmbitusAbsoluteSemitones"
AMBITUS_MEAN_INTERVAL = "AmbitusMeanInterval"
AMBITUS_MEAN_SEMITONES = "AmbitusMeanSemitones"


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:

    this_aria_ambitus = part_data["ambitus_solution"]
    lowest_note, highest_note = part_data["ambitus_pitch_span"]
    lowest_note_text = lowest_note.nameWithOctave.replace("-", "b")
    highest_note_text = highest_note.nameWithOctave.replace("-", "b")
    lowest_index = int(lowest_note.ps)
    highest_index = int(highest_note.ps)
    joined_notes = ",".join([lowest_note_text, highest_note_text])

    return {
        LOWEST_NOTE: lowest_note_text,
        HIGHEST_NOTE: highest_note_text,
        LOWEST_INDEX: lowest_index,
        HIGHEST_INDEX: highest_index,
        LOWEST_MEAN_NOTE: lowest_note_text,
        LOWEST_MEAN_INDEX: lowest_index,
        HIGHEST_MEAN_NOTE: highest_note_text,
        HIGHEST_MEAN_INDEX: highest_index,
        AMBITUS_LARGEST_INTERVAL: this_aria_ambitus.name,
        AMBITUS_LARGEST_SEMITONES: this_aria_ambitus.semitones,
        AMBITUS_SMALLEST_INTERVAL: this_aria_ambitus.name,
        AMBITUS_SMALLEST_SEMITONES: this_aria_ambitus.semitones,
        AMBITUS_ABSOLUTE_INTERVAL: joined_notes,
        AMBITUS_ABSOLUTE_SEMITONES: joined_notes,
        AMBITUS_MEAN_INTERVAL: joined_notes,
        AMBITUS_MEAN_SEMITONES: joined_notes,
    }
