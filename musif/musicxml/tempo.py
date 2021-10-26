import re
import xml.etree.ElementTree as ET
from enum import Enum
from typing import Optional


class TempoGroup2(Enum):
    ND = "nd"
    SLOW = "Slow"
    MODERATE = "Moderate"
    FAST = "Fast"


def get_time_signature_type(timesignature):
    if timesignature in ['1/2', '1/4', '1/8', '1/16', '2/2', '2/4', '2/8', '2/16', '4/4', 'C', '4/2', '4/8', '4/16', '8/2', '8/4', '8/8', '8/16']:
        return 'simple duple'
    elif timesignature in ['6/8', '3/8', '12/2', '12/4', '12/8', '12/16']:
        return 'compound duple'
    elif timesignature in ['3/2', '3/4', '3/16', '6/2', '6/4', '6/16']:
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


def get_tempo_grouped_2(tempo_grouped_1: str) -> TempoGroup2:

    if tempo_grouped_1 is None or tempo_grouped_1.lower() == 'nd':
        return TempoGroup2.ND
    possible_terminations = ['ino', 'etto', 'ietto', 'ssimo', 'issimo', 'hetto']
    slow_basis = ['Adagio', 'Affettuoso', 'Grave', 'Sostenuto', 'Largo', 'Lento', 'Sostenuto']
    slow = slow_basis + [w[:-1] + t for w in slow_basis for t in possible_terminations]
    moderate_basis = ['Andante', 'Arioso', 'Comodo', 'Cantabile', 'Comodo', 'Espressivo', 'Grazioso', 'Gustoso', 'Maestoso', 'Minueto', 'Moderato', 'Marcía',
                      'Amoroso']
    moderate = moderate_basis + [w[:-1] + t for w in moderate_basis for t in possible_terminations]
    fast_basis = ['Agitato', 'Allegro', 'Con brio', 'Spiritoso', 'Fiero', 'Presto', 'Risoluto', 'Vivace']
    fast = fast_basis + [w[:-1] + t for w in fast_basis for t in possible_terminations]

    if tempo_grouped_1 in ['A tempo', 'Giusto']:
        return TempoGroup2.ND
    elif tempo_grouped_1 in slow:
        return TempoGroup2.SLOW
    elif tempo_grouped_1 in moderate:
        return TempoGroup2.MODERATE
    elif tempo_grouped_1 in fast:
        return TempoGroup2.FAST


def get_number_of_beats(time_signature: str) -> int:
    time_signature = time_signature.split(",")[0]
    if time_signature in ['1/2', '1/4', '1/8', '1/16','3/8']:
        return 1
    if time_signature in ['2/2', '2/4', '2/8', '2/16', '6/8', '6/2', '6/4', '6/16']:
        return 2
    if time_signature in ['3/2', '3/4', '3/16', '9/2', '9/4', '9/8', '9/16']:
        return 3
    if time_signature in ['4/4', '4/2', '4/8', '4/16', 'C', '12/2', '12/4', '12/8', '12/16']:
        return 4
    if time_signature in ['8/2', '8/4', '8/8', '8/16']:
        return 8


def extract_numeric_tempo(file_path: str) -> Optional[int]:
    tree = ET.parse(file_path)
    root = tree.getroot()
    try:
        tempo = int(root.find("part").find("measure").find("direction").find("sound").get("tempo"))
    except:
        tempo = None
    return tempo
