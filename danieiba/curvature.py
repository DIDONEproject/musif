from glob import glob

from music21.chord import Chord
from music21.converter import parse
from music21.note import Rest
from music21.stream import Measure
from tqdm import tqdm

from musif.common._utils import read_lines_from_txt_file, write_dicts_to_csv

if __name__ == "__main__":
    aria_ids = list(read_lines_from_txt_file("arias.csv"))
    for aria_id in tqdm(aria_ids):
        notes = []
        file_path = glob(f'../../Corpus/xml/*{aria_id}*.xml')[0]
        score = parse(file_path)
        for part in score.parts:
            if len(part.lyrics()) > 0:
                break
        else:  # Voice part couldn't be found
            continue
        time_signature = list(part.getTimeSignatures())[0].ratioString
        for measure in part.getElementsByClass(Measure):
            notes_and_rests = list(measure.notesAndRests)
            for note_or_rest in notes_and_rests:
                if isinstance(note_or_rest, Chord):
                    for chord_note in note_or_rest.notes:
                        if chord_note.hasStyleInformation and chord_note.style.noteSize != "cue":
                            note_or_rest = chord_note
                            break
                    else:
                        note_or_rest = note_or_rest.notes[0]
                pitch = None if isinstance(note_or_rest, Rest) else note_or_rest.pitch.midi
                duration = note_or_rest.duration.quarterLength  # / note_or_rest.beatDuration.quarterLength
                notes.append({"pitch": pitch, "duration": duration})
        write_dicts_to_csv(notes, f"curvature_files/{aria_id}.csv")
