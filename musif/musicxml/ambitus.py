from typing import List, Tuple

from music21.note import Note


def get_notes_ambitus(notes: List[Note]) -> Tuple[Note, Note]:
    lowest_note = notes[0]
    highest_note = notes[1]
    for i in range(1, len(notes)):
        note_index = notes[i].pitch.midi
        if note_index < lowest_note.pitch.midi:
            lowest_note = notes[i]
        if note_index > highest_note.pitch.midi:
            highest_note = notes[i]
    return lowest_note, highest_note
