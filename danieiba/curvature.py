from glob import glob

import pandas as pd
from music21.converter import parse
from music21.note import Note, Rest
from music21.stream import Measure, Part

from musif.common.utils import read_lines_from_txt_file

if __name__ == "__main__":
    aria_ids = list(read_lines_from_txt_file("arias.csv"))
    for aria_id in aria_ids:
        pitches = []
        durations = []
        file_path = glob(f'../../Corpus/xml/*{aria_id}*.xml')[0]
        score = parse(file_path)
        for part in score.parts:
            if part.id.isupper():
                break
        for measure in part.getElementsByClass(Measure):
            notes_and_rests = list(measure.notesAndRests)
            for note_or_rest in notes_and_rests:
                if isinstance(note_or_rest, Rest):
                    pitch = -1
                else:
                    pitch = note_or_rest.pitch.midi
                duration = note_or_rest.duration.quarterLength / note_or_rest.beatDuration.quarterLength
                pitches.append(pitch)
                durations.append(duration)
        print()
