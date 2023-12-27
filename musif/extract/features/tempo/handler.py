from enum import Enum
from typing import List

from music21.expressions import TextExpression
from music21.stream import Measure

from musif.cache import isinstance
from musif.config import ExtractConfiguration
from musif.extract.constants import (
    DATA_NUMERIC_TEMPO,
    DATA_PART,
    DATA_SCORE,
    GLOBAL_TIME_SIGNATURE,
)
from musif.musicxml.tempo import (
    get_number_of_beats,
    get_tempo_grouped_1,
    get_tempo_grouped_2,
    get_time_signature_type,
)

from . import constants as C


class TempoGroup2(Enum):
    NA = "NA"
    SLOW = "Slow"
    MODERATE = "Moderate"
    FAST = "Fast"


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    part = part_data[DATA_PART]

    (
        time_signature,
        measures,
        time_signatures,
        time_signature_grouped,
        number_of_beats,
    ) = extract_time_signatures(list(part.getElementsByClass(Measure)), score_data)
    part_data.update(
        {
            C.TIME_SIGNATURES: time_signatures,
            C.TS_MEASURES: measures,
        }
    )
    part_features.update(
        {
            C.TIME_SIGNATURE: time_signature,
            C.TIME_SIGNATURE_GROUPED: time_signature_grouped,
            C.NUMBER_OF_BEATS: number_of_beats,
        }
    )


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):

    score = score_data[DATA_SCORE]
    # for the features, we use the first part as reference!
    part = score.parts[0]
    numeric_tempo, tempo_mark = extract_tempo(score_data, part)
    tempo_grouped_1 = get_tempo_grouped_1(tempo_mark)
    tempo_grouped_2 = get_tempo_grouped_2(tempo_grouped_1)

    (
        time_signature,
        measures,
        time_signatures,
        time_signature_grouped,
        number_of_beats,
    ) = extract_time_signatures(list(part.getElementsByClass(Measure)), score_data)

    score_features.update(
        {
            C.TEMPO: tempo_mark,
            C.NUMERIC_TEMPO: numeric_tempo,
            C.TIME_SIGNATURE: time_signature,
            C.TIME_SIGNATURE_GROUPED: time_signature_grouped,
            C.NUMBER_OF_BEATS: number_of_beats,
            C.TEMPO_GROUPED_1: tempo_grouped_1,
            C.TEMPO_GROUPED_2: tempo_grouped_2,
        }
    )


def extract_time_signatures(measures: list, score_data: dict) -> tuple:
    """
    Extracts time signatures from a list of measures and returns relevant information.

    Args:
        measures (list): A list of measures.
        score_data (dict): A dictionary containing score data.

    Returns:
        tuple: A tuple containing the time signature, dictionary of measures and their
        indices, list of time signatures, time signature type, and number of beats.

    The function extracts time signatures from a list of measures and returns
    relevant information. The function takes two arguments, measures and
    score_data. measures is a list of measures and score_data is a dictionary
    containing score data. The function returns a tuple containing the time
    signature, dictionary of measures and their indices, list of time signatures,
    time signature type, and number of beats.

    The function ases `'NA'` as the time signature if no time signature is found
    in the score.
    """

    ts_measures = {}
    time_signatures = []
    for i, element in enumerate(measures):
        if element.measureNumber not in ts_measures:
            if element.timeSignature is not None:
                time_signatures.append(element.timeSignature.ratioString)
            else:
                if len(time_signatures) >= 1:
                    time_signatures.append(time_signatures[-1])
                elif hasattr(score_data.get(GLOBAL_TIME_SIGNATURE), 'ratioString'):
                    time_signatures.append(
                        score_data[GLOBAL_TIME_SIGNATURE].ratioString
                    )
                else:
                    time_signatures.append("NA")

            ts_measures[element.measureNumber] = i
        else:
            time_signatures.append(time_signatures[ts_measures[element.measureNumber]])

    time_signatures_set = set(time_signatures)
    time_signature = list(sorted(time_signatures_set, key=time_signatures.index))[0] if time_signatures_set else ''

    time_signature_grouped = get_time_signature_type(time_signature)
    number_of_beats = get_number_of_beats(time_signature)

    return (
        time_signature,
        ts_measures,
        time_signatures,
        time_signature_grouped,
        number_of_beats,
    )


def extract_tempo(score_data, part):
    numeric_tempo = score_data[DATA_NUMERIC_TEMPO]
    tempo_mark = TempoGroup2.NA.value
    for measure in part:
        if isinstance(measure, Measure):
            for element in measure:
                if isinstance(element, TextExpression):
                    if get_tempo_grouped_1(element.content) != "NA":
                        tempo_mark = element.content
            break  # only take into account the first bar!
    return numeric_tempo, tempo_mark
