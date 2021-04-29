import re
from collections import Counter
from enum import Enum
from typing import List

from music21.expressions import TextExpression
from music21.stream import Measure

from musif.config import Configuration
from musif.extract.features.prefix import get_corpus_prefix

TEMPO = "Tempo"
TIME_SIGNATURE = "TimeSignature"
TIME_SIGNATURE_GROUPED = "TimeSignatureGrouped"
TEMPO_GROUPED_1 = "TempoGrouped1"
TEMPO_GROUPED_2 = "TempoGrouped2"


class TempoGroup2(Enum):
    ND = "nd"
    SLOW = "Slow"
    MODERATE = "Moderate"
    FAST = "Fast"


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:

    # cogemos la part de la voz, y de ahí sacamos el time signature, aparte de devolverla para su posterior uso
    # cambiamos la forma de extraer la voz --- se hace con el atributo de part, 'instrumentSound'. Este atributo
    # indica el tipo de instrumento y por ultimo el nombre. voice.soprano, strings.violin o strings.viola

    time_signatures = []
    for partVoice in score_data["parts"]:
        m = list(partVoice.getTimeSignatures())
        time_signature = m[0].ratioString
        time_signatures.append(time_signature)

    tempo_mark = "ND"
    for measure in score_data["score"].parts[0]:
        if isinstance(measure, Measure):
            for element in measure:
                if isinstance(element, TextExpression):
                    if get_tempo_grouped_1(element.content) != "ND":
                        tempo_mark = element.content
                        break
            break  # only take into account the first bar!
    time_signature = ",".join(list(set(time_signatures)))
    time_signature_grouped = get_time_signature_type(time_signature)
    tg1 = get_tempo_grouped_1(tempo_mark)
    tg2 = get_tempo_grouped_2(tg1).value

    return {
        TEMPO: tempo_mark,
        TIME_SIGNATURE: time_signature,
        TIME_SIGNATURE_GROUPED: time_signature_grouped,
        TEMPO_GROUPED_1: tg1,
        TEMPO_GROUPED_2: tg2,
    }


def get_corpus_features(scores_data: List[dict], parts_data: List[dict], cfg: Configuration, scores_features: List[dict], corpus_features: dict) -> dict:
    features = {}
    corpus_prefix = get_corpus_prefix()
    tempo_grouped_2_counter = Counter([score_features[TEMPO_GROUPED_2] for score_features in scores_features])
    time_signature_counter = Counter([score_features[TIME_SIGNATURE] for score_features in scores_features])
    time_signature_grouped_counter = Counter([score_features[TIME_SIGNATURE_GROUPED] for score_features in scores_features])
    for group in TempoGroup2:
        count = tempo_grouped_2_counter.get(group.value, 0)
        features[f"{corpus_prefix}{TEMPO_GROUPED_2}_{group.value}"] = count
    for group, count in time_signature_counter.items():
        formatted_group = group if group else 'nd'
        features[f"{corpus_prefix}{TIME_SIGNATURE}_{formatted_group}"] = count
    for group, count in time_signature_grouped_counter.items():
        formatted_group = ''.join([word.capitalize() for word in group.split(" ")])
        features[f"{corpus_prefix}{TIME_SIGNATURE_GROUPED}_{formatted_group}"] = count
    return features


def get_time_signature_type(timesignature):
    # this function classifies time signatures
    if timesignature in ['1/2', '1/4', '1/8', '1/16', '2/2', '2/4', '2/8', '2/16', '4/4', 'C', '4/2', '4/8', '4/16', '8/2', '8/4', '8/8', '8/16']:
        return 'simple duple'
    elif timesignature in ['6/8', '12/2', '12/4', '12/8', '12/16']:
        return 'compound duple'
    elif timesignature in ['3/2', '3/4', '3/8', '3/16', '6/2', '6/4', '6/16']:
        return 'simple triple'
    elif timesignature in ['9/2', '9/4', '9/8', '9/16']:
        return 'compound triple'
    else:
        return 'other'


def get_tempo_grouped_1(tempo):
    """
    data cleaning; returns a 1st level of grouping for the tempo markings, removing secondary labels and diminutive endings
    """
    tempo = re.sub('\\W+', ' ', tempo)  # removes eventual special characters
    replacements = [(w, '') for w in ['molto', 'poco', 'un poco', 'tanto', 'un tanto', 'assai', 'meno', 'più', 'piuttosto']]
    # tempo = tempo.strip()
    if not tempo:
        return 'ND'

    for r in replacements:
        tempo = tempo.replace(*r)
    tempo = tempo.replace("Con brio", 'brio').replace('con brio', 'brio').replace('Con spirito', 'spiritoso').replace('con spirito', 'spiritoso')
    ################ FIRST IMPORTANT WORDS ################
    # Important words. If the tempo marking contains any of them, it determines the grouping
    base_important_words = ['adagio', "allegro", "andante", "andantino", "largo", "lento", "presto", "vivace", 'minueto']
    # if the tempo marking ends in -ietto and or -issimo, it retuns the marking without that ending
    important_words = base_important_words + [w[0:-1] + 'etto' for w in base_important_words] + [w[0:-1] + 'ietto' for w in base_important_words] + [
        w[0:-1] + 'issimo' for w in base_important_words] + [w[0:-1] + 'ssimo' for w in base_important_words] + [w[0:-1] + 'hetto' for w in
                                                                                                                 base_important_words]

    last_words = ''
    for word in tempo.split(" "):
        if word.lower() in important_words and ('ma non' not in last_words or ' ma ' not in last_words or 'Tempo di' in last_words):
            return word.capitalize()
        last_words += ' ' + word

    ################ SECOND IMPORTANT WORDS ################
    relevant_words = ['amoroso', 'affettuoso', 'agitato', 'arioso', 'cantabile', 'comodo', 'brio', 'spiritoso', 'espressivo', 'fiero', 'giusto', 'grave',
                      'grazioso', 'gustoso', 'maestoso', 'moderato', 'risoluto', 'sostenuto', 'spiritoso', 'tempo']
    words_contained = []
    for word in tempo.split(" "):
        if word.lower() in relevant_words:
            words_contained.append(word)
    ## FINAL DECISION (Two exceptions: tempo and con brio) ##
    if len(words_contained) == 1:
        if words_contained[0].lower() not in ['tempo', 'brio']:
            return words_contained[0].capitalize()
        elif words_contained[0].lower() == 'tempo':
            return 'A tempo'
        else:
            return 'Con brio'
    elif len(words_contained) > 1:
        for w in words_contained:
            if w[0].isupper():
                if w.lower() != 'tempo':
                    return w  # returns the capitalized term
                elif w.lower() == 'tempo':
                    return 'A tempo'
                else:
                    return 'Con brio'
        if words_contained[0] != 'tempo':
            return words_contained[0].capitalize()
        elif words_contained[0] == 'tempo':
            return 'A tempo'  # or the first one
        else:
            return 'Con brio'

    # print('Sorry, we can\'t group the tempo', tempo)
    return 'ND'


def get_tempo_grouped_2(TempoGrouped1) -> TempoGroup2:
    possible_terminations = ['ino', 'etto', 'ietto', 'ssimo', 'issimo', 'hetto']
    slow_basis = ['Adagio', 'Affettuoso', 'Grave', 'Sostenuto', 'Largo', 'Lento', 'Sostenuto']
    slow = slow_basis + [w[:-1] + t for w in slow_basis for t in possible_terminations]
    moderate_basis = ['Andante', 'Arioso', 'Comodo', 'Cantabile', 'Comodo', 'Espressivo', 'Grazioso', 'Gustoso', 'Maestoso', 'Minueto', 'Moderato', 'Marcía',
                      'Amoroso']
    moderate = moderate_basis + [w[:-1] + t for w in moderate_basis for t in possible_terminations]
    fast_basis = ['Agitato', 'Allegro', 'Con brio', 'Spiritoso', 'Fiero', 'Presto', 'Risoluto', 'Vivace']
    fast = fast_basis + [w[:-1] + t for w in fast_basis for t in possible_terminations]

    if TempoGrouped1 in ['A tempo', 'Giusto']:
        return TempoGroup2.ND
    elif TempoGrouped1 in slow:
        return TempoGroup2.SLOW
    elif TempoGrouped1 in moderate:
        return TempoGroup2.MODERATE
    elif TempoGrouped1 in fast:
        return TempoGroup2.FAST

