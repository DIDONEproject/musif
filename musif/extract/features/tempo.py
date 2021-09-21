from enum import Enum
from typing import List

from music21.expressions import TextExpression
from music21.stream import Measure

from musif.config import Configuration
from musif.constants import DATA_PART, DATA_SCORE, DATA_FILE
from musif.musicxml.tempo import get_time_signature_type, get_number_of_beats, extract_numeric_tempo, \
    get_tempo_grouped_1, get_tempo_grouped_2


TEMPO = "Tempo"
NUMERIC_TEMPO = "NumericTempo"
TIME_SIGNATURE = "TimeSignature"
TIME_SIGNATURE_GROUPED = "TimeSignatureGrouped"
TEMPO_GROUPED_1 = "TempoGrouped1"
TEMPO_GROUPED_2 = "TempoGrouped2"
NUMBER_OF_BEATS = "NumberOfBeats"


class TempoGroup2(Enum):
    ND = "nd"
    SLOW = "Slow"
    MODERATE = "Moderate"
    FAST = "Fast"


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    part = part_data[DATA_PART]
    time_signature = list(part.getTimeSignatures())[0].ratioString
    time_signature_grouped = get_time_signature_type(time_signature)
    number_of_beats = get_number_of_beats(time_signature)
    part_features.update({
        TIME_SIGNATURE: time_signature,
        TIME_SIGNATURE_GROUPED: time_signature_grouped,
        NUMBER_OF_BEATS: number_of_beats
    })


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):

    # cogemos la part de la voz, y de ahí sacamos el time signature, aparte de devolverla para su posterior uso
    # cambiamos la forma de extraer la voz --- se hace con el atributo de part, 'instrumentSound'. Este atributo
    # indica el tipo de instrumento y por ultimo el nombre. voice.soprano, strings.violin o strings.viola

    score = score_data[DATA_SCORE]
    numeric_tempo = extract_numeric_tempo(score_data[DATA_FILE])
    time_signatures = []
    for part in score.parts:
        m = list(part.getTimeSignatures())
        time_signature = m[0].ratioString
        time_signatures.append(time_signature)

    tempo_mark = "ND"
    for measure in score.parts[0]:
        if isinstance(measure, Measure):
            for element in measure:
                if isinstance(element, TextExpression):
                    if get_tempo_grouped_1(element.content) != "ND":
                        tempo_mark = element.content
                        # break
            break  # only take into account the first bar!
    time_signature = ",".join(list(set(time_signatures)))
    time_signature_grouped = get_time_signature_type(time_signature)
    tg1 = get_tempo_grouped_1(tempo_mark)
    tg2 = get_tempo_grouped_2(tg1).value
    number_of_beats = get_number_of_beats(time_signature)

    score_features.update({
        TEMPO: tempo_mark,
        NUMERIC_TEMPO: numeric_tempo,
        TIME_SIGNATURE: time_signature,
        TIME_SIGNATURE_GROUPED: time_signature_grouped,
        TEMPO_GROUPED_1: tg1,
        TEMPO_GROUPED_2: tg2,
        NUMBER_OF_BEATS: number_of_beats,
    })
