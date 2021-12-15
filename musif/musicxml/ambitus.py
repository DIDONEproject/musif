from typing import List, Optional, Tuple

from music21.chord import Chord
from music21.note import Note


def get_notes_ambitus(notes: List[Note]) -> Tuple[Note, Note]:
    first_note = notes[0] if isinstance(notes[0], Chord) else notes[0]
    lowest_note = first_note
    highest_note = first_note
    for note in notes[1:]:
        current_note = note[0] if isinstance(note, Chord) else note
        if current_note.pitch.midi < lowest_note.pitch.midi:
            lowest_note = current_note
        if current_note.pitch.midi > highest_note.pitch.midi:
            highest_note = current_note
    return lowest_note, highest_note
