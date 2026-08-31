"""Generate the synthetic regression score committed at
tests/data/scores/TestComposer_synthetic_piece.xml.

The score is designed to exercise the extractor's edge cases: dotted figures,
a full-measure rest, chromatic unisons and repeated notes, a large descending
leap, dynamics with a rest reset, lyrics with a melisma, and a metre change.

Run from the repository root:  python tests/data/make_synthetic_score.py
"""
from pathlib import Path

from music21 import instrument, stream
from music21.dynamics import Dynamic
from music21.meter import TimeSignature
from music21.note import Note, Rest


def _measure(number, elements, time_signature=None):
    measure = stream.Measure(number=number)
    if time_signature is not None:
        measure.append(TimeSignature(time_signature))
    for element in elements:
        measure.append(element)
    return measure


def note(pitch, quarter_length=1.0, lyric=None):
    n = Note(pitch, quarterLength=quarter_length)
    if lyric is not None:
        n.lyric = lyric
    return n


def build_score() -> stream.Score:
    score = stream.Score()

    violin = stream.Part()
    violin.partName = "Violin I"
    violin.insert(0, instrument.Violin())
    violin.append(_measure(1, [Dynamic("f"), note("C5"), note("D5"), note("E5"), note("F5")], "4/4"))
    violin.append(_measure(2, [note("G5", 0.75), note("A5", 0.25), note("B5"), note("C6"), note("G5")]))
    violin.append(_measure(3, [Rest(quarterLength=4.0)]))
    violin.append(_measure(4, [note("C5"), note("C#5"), note("C5"), note("C5")]))
    violin.append(_measure(5, [note("C6"), note("C4"), Dynamic("p"), note("E5", 2.0)]))
    violin.append(_measure(6, [note("F5"), note("E5"), note("D5"), note("C5")]))
    violin.append(_measure(7, [note("E5"), note("D5"), note("C5")], "3/4"))
    violin.append(_measure(8, [note("C5", 3.0)]))
    score.append(violin)

    soprano = stream.Part()
    soprano.partName = "Soprano"
    soprano.insert(0, instrument.Soprano())
    soprano.append(_measure(1, [note("E4", 2.0, "Al"), note("G4", 2.0, "ma")], "4/4"))
    soprano.append(_measure(2, [note("A4", 1.0, "del"), note("B4", 1.0), note("C5", 2.0, "cor")]))
    soprano.append(_measure(3, [Rest(quarterLength=4.0)]))
    soprano.append(_measure(4, [note("C5", 2.0, "vie"), note("B4", 1.0), note("A4", 1.0)]))
    soprano.append(_measure(5, [note("G4", 4.0, "ni")]))
    soprano.append(_measure(6, [note("A4", 2.0, "a"), note("F4", 2.0, "me")]))
    soprano.append(_measure(7, [note("E4", 2.0, "gia"), note("D4", 1.0)], "3/4"))
    soprano.append(_measure(8, [note("C4", 3.0, "mai")]))
    score.append(soprano)

    cello = stream.Part()
    cello.partName = "Violoncello"
    cello.insert(0, instrument.Violoncello())
    cello.append(_measure(1, [note("C3", 2.0), note("G3", 2.0)], "4/4"))
    cello.append(_measure(2, [note("E3", 2.0), note("C3", 2.0)]))
    cello.append(_measure(3, [note("G2", 4.0)]))
    cello.append(_measure(4, [note("A2", 2.0), note("F2", 2.0)]))
    cello.append(_measure(5, [note("C3", 2.0), note("C2", 2.0)]))
    cello.append(_measure(6, [note("F2", 2.0), note("G2", 2.0)]))
    cello.append(_measure(7, [note("G2", 3.0)], "3/4"))
    cello.append(_measure(8, [note("C2", 3.0)]))
    score.append(cello)

    return score


if __name__ == "__main__":
    destination = Path(__file__).parent / "scores" / "TestComposer_synthetic_piece.xml"
    build_score().write("musicxml", fp=str(destination))
    print(f"written {destination}")
