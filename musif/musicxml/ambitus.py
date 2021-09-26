from typing import Tuple

from music21.analysis.discrete import Ambitus
from music21.stream import Part


def get_part_ambitus(part: Part) -> Tuple:
    ambitus = Ambitus()
    ambitus_solution = ambitus.getSolution(part)
    ambitus_pitch_span = ambitus.getPitchSpan(part)
    return ambitus_solution, ambitus_pitch_span
