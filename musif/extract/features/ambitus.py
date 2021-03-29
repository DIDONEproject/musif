from music21 import analysis

from musif.config import Configuration


def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:

    part = part_data["part"]
    ambitus = analysis.discrete.Ambitus()
    this_aria_ambitus = ambitus.getSolution(part)
    lowest_note, highest_note = ambitus.getPitchSpan(part)
    lowest_note_text = lowest_note.nameWithOctave.replace("-", "b")
    highest_note_text = highest_note.nameWithOctave.replace("-", "b")
    lowest_index = int(lowest_note.ps)
    highest_index = int(highest_note.ps)
    joined_notes = ",".join([lowest_note_text, highest_note_text])

    return {
        "LowestNote": lowest_note_text,
        "HighestNote": highest_note_text,
        "LowestIndex": lowest_index,
        "HighestIndex": highest_index,
        "LowestMeanNote": lowest_note_text,
        "LowestMeanIndex": lowest_index,
        "HighestMeanNote": highest_note_text,
        "HighestMeanIndex": highest_index,
        "AmbitusLargestInterval": this_aria_ambitus.name,
        "AmbitusLargestSemitones": this_aria_ambitus.semitones,
        "AmbitusSmallestInterval": this_aria_ambitus.name,
        "AmbitusSmallestSemitones": this_aria_ambitus.semitones,
        "AmbitusAbsoluteInterval": joined_notes,
        "AmbitusAbsoluteSemitones": joined_notes,
        "AmbitusMeanInterval": joined_notes,
        "AmbitusMeanSemitones": joined_notes,
    }
