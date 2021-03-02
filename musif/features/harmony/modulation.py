from music21.stream import Part
from pandas import DataFrame


def compute_modulations(part: Part, part_expanded: Part, modulations: list) -> DataFrame:
    """
    This function generates a dataframe with the measures and the local key
    present in each one of them based on the 'modulations' atribute in the json
    """
    measures = [m.measureNumber for m in part]
    measures_expanded = [m.measureNumber for m in part_expanded]

    first_modulation = modulations[0]
    key = []
    for m in modulations[1:]:
        key += [first_modulation[0]] * measures.index(m[1] - first_modulation[1] + 1)
        first_modulation = m
    key += [first_modulation[0]] * (measures[-1] - first_modulation[1] + 1)
    if measures[-1] != measures_expanded[-1]:  # there are repetitions TODO: test
        measures_expanded = measures_expanded[measures_expanded.index(measures[-1]):]  # change the starting point
        first_modulation = modulations[0]
        for m in modulations[1:]:
            if m[1] <= len(measures_expanded):
                key += [first_modulation[0]] * measures_expanded.index(m[1] - first_modulation[1] + 1)
                first_modulation = m
    return DataFrame({'measures_continued': measures_expanded, 'key': key})
