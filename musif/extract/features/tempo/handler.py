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
    time_signature = list(part.getTimeSignatures())[0].ratioString
    time_signature_grouped = get_time_signature_type(time_signature)
    number_of_beats = get_number_of_beats(time_signature)
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

    # cogemos la part de la voz, y de ahí sacamos el time signature, aparte de
    # devolverla para su posterior uso cambiamos la forma de extraer la voz --- se hace
    # con el atributo de part, 'instrumentSound'. Este atributo indica el tipo de
    # instrumento y por ultimo el nombre. voice.soprano, strings.violin o strings.viola
    # for part in score.parts:
    # m = list(part.getTimeSignatures())
    # time_signature = m[0].ratioString
    # time_signatures.append(time_signature)

    score = score_data[DATA_SCORE]
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

    score_data.update(
        {
            C.TIME_SIGNATURE: time_signature,
            C.TIME_SIGNATURES: time_signatures,
            C.TS_MEASURES: measures,
        }
    )

    score_features.update(
        {
            C.TEMPO: tempo_mark,
            C.NUMERIC_TEMPO: numeric_tempo,
            C.TIME_SIGNATURE: time_signature.split(",")[0],
            C.TIME_SIGNATURE_GROUPED: time_signature_grouped,
            C.TEMPO_GROUPED_1: tempo_grouped_1,
            C.TEMPO_GROUPED_2: tempo_grouped_2,
            C.NUMBER_OF_BEATS: number_of_beats,
        }
    )


def extract_time_signatures(measures: list, score_data: dict):
    ts_measures = []
    time_signatures = []
    for i, element in enumerate(measures):
        ts_measures.append(element.measureNumber)
        if element.measureNumber not in ts_measures[:-1]:
            if element.timeSignature:
                time_signatures.append(element.timeSignature.ratioString)
            else:
                if len(time_signatures) >= 1:
                    time_signatures.append(time_signatures[-1])
                elif GLOBAL_TIME_SIGNATURE in score_data:
                    time_signatures.append(
                        score_data[GLOBAL_TIME_SIGNATURE].ratioString
                    )
                else:
                    raise Exception("There was an error when omputing time signatures of the score.")
                    
        else:
            time_signatures.append(
                time_signatures[ts_measures.index(element.measureNumber)]
            )

    time_signatures_set = set(time_signatures)
    time_signature = ",".join(
        list(sorted(time_signatures_set, key=time_signatures.index))
    )
    time_signature_grouped = get_time_signature_type(time_signature.split(",")[0])
    number_of_beats = get_number_of_beats(time_signature.split(",")[0])

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

