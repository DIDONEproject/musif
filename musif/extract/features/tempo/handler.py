from enum import Enum
from typing import List

from music21.expressions import TextExpression
from music21.stream import Measure

from musif.config import Configuration
from musif.extract.constants import DATA_FILE, DATA_PART, DATA_SCORE
from musif.musicxml.tempo import extract_numeric_tempo, get_number_of_beats, get_tempo_grouped_1, get_tempo_grouped_2, \
    get_time_signature_type
from .constants import *


class TempoGroup2(Enum):
    ND = "NA"
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
    # for part in score.parts:
        # m = list(part.getTimeSignatures())
        # time_signature = m[0].ratioString
        # time_signatures.append(time_signature)

    score = score_data[DATA_SCORE]
    part = score.parts[0]
    numeric_tempo, tempo_mark = ExtractTempo(score_data, part)
    tg1 = get_tempo_grouped_1(tempo_mark)
    tg2 = get_tempo_grouped_2(tg1).value

    time_signature, measures, time_signatures, time_signature_grouped, number_of_beats = Extract_Time_Signatures(list(part.getElementsByClass(Measure)))
    
    score_data.update({
        TIME_SIGNATURE: time_signature,
        TIME_SIGNATURES:  time_signatures,
        TS_MEASURES: measures        
    })
    
    score_features.update({
        TEMPO: tempo_mark,
        NUMERIC_TEMPO: numeric_tempo,
        TIME_SIGNATURE: time_signature,
        TIME_SIGNATURE_GROUPED: time_signature_grouped,
        TEMPO_GROUPED_1: tg1,
        TEMPO_GROUPED_2: tg2,
        NUMBER_OF_BEATS: number_of_beats,
    })

def Extract_Time_Signatures(measures):
    ts_measures=[]
    time_signatures = []
    for i, element in enumerate(measures):
        ts_measures.append(element.measureNumber)
        if element.measureNumber not in ts_measures[:-1]:
            if element.timeSignature:
                time_signatures.append(element.timeSignature.ratioString)
            else:
                time_signatures.append(time_signatures[i-1])
        else: #therothetically this works when repetitions are taken into consideration
            time_signatures.append(time_signatures[ts_measures.index(element.measureNumber)])

    time_signature = ",".join(list(sorted(set(time_signatures), key=time_signatures.index)))
    time_signature_grouped = get_time_signature_type(time_signature.split(',')[0])
    number_of_beats = get_number_of_beats(time_signature.split(',')[0])

    return time_signature, ts_measures, time_signatures, time_signature_grouped, number_of_beats


def ExtractTempo(score_data, part):
    numeric_tempo = extract_numeric_tempo(score_data[DATA_FILE])
    tempo_mark = "NA"
    for measure in part:
        if isinstance(measure, Measure):
            for element in measure:
                if isinstance(element, TextExpression):
                    if get_tempo_grouped_1(element.content) != "NA":
                        tempo_mark = element.content
            break  # only take into account the first bar!
    return numeric_tempo,tempo_mark
