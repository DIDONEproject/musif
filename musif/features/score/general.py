import re

from music21.expressions import TextExpression
from music21.stream import Measure, Score


def get_general_features(score: Score) -> dict:
    # s = converter.parse(xml_file)
    my_key = score.analyze("key")
    key_mode = my_key.mode
    key_name = (
        my_key.name.split(" ")[0].strip().replace("-", "b")
    )  # coger solo la string de antes del espacio? y así quitar major y minor
    key_name = key_name if key_mode == "major" else key_name.lower()

    key_signature = str()
    if my_key.sharps:
        key_signature = "b" * abs(my_key.sharps) if my_key.sharps < 0 else "s" * my_key.sharps
    else:
        key_signature = "n"

    # cogemos la part de la voz, y de ahí sacamos el time signature, aparte de devolverla para su posterior uso
    # cambiamos la forma de extraer la voz --- se hace con el atributo de part, 'instrumentSound'. Este atributo
    # indica el tipo de instrumento y por ultimo el nombre. voice.soprano, strings.violin o strings.viola

    time_signatures = []
    for partVoice in score.parts:
        m = list(partVoice.getTimeSignatures())
        time_signature = m[0].ratioString
        time_signatures.append(time_signature)

    tempo_mark = "ND"
    for measure in score.parts[0]:
        if isinstance(measure, Measure):
            for element in measure:
                if isinstance(element, TextExpression):
                    if get_TempoGrouped1(element.content) != "ND":
                        tempo_mark = element.content
                        break
            break  # only take into account the first bar!

    return {
        "Key": key_name,
        "Mode": key_mode,
        "KeySignature": key_signature,
        "Tempo": tempo_mark,
        "TimeSignature": ",".join(list(set(time_signatures))),
    }


def get_abbreviated_key(full_key: str) -> str:
    """
    returns abbreviated designation of keys (uppercase for major mode; lowercase for minor mode)
    example: if key == 'D- major': return 'Db'
    """
    key_parts = full_key.split(' ')
    mode = key_parts[1].strip().lower()
    tonality = key_parts[0].strip()
    tonality = tonality.lower() if mode == 'minor' else tonality.capitalize()
    tonality = tonality.replace('-', 'b')  # if the character '-' is not in the string, nothing will change
    return tonality


def get_final(key):
    """
    returns 1st degree of the scale (in uppercase)
    example: if key in ['C- major', 'c- minor']: return 'Cb'
    """
    tonalty = key.split(' ')[0]
    tonalty = tonalty.upper()
    return tonalty.replace('-', 'b')  # if the character '-' is not in the string, nothing will change


def get_mode(key: str) -> str:
    if key.isupper():
        return 'M'
    else:
        return 'm'


def get_KeySignatureType(keysignature):
    """
    returns the key signature type ('bb) for flats, 'ss' for sharps, and 'nn' for naturals
    """
    return keysignature[0]


def get_TempoGrouped1(tempo):
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


def get_TempoGrouped2(TempoGrouped1):
    possible_terminations = ['ino', 'etto', 'ietto', 'ssimo', 'issimo', 'hetto']
    slow_basis = ['Adagio', 'Affettuoso', 'Grave', 'Sostenuto', 'Largo', 'Lento', 'Sostenuto']
    slow = slow_basis + [w[:-1] + t for w in slow_basis for t in possible_terminations]
    moderate_basis = ['Andante', 'Arioso', 'Comodo', 'Cantabile', 'Comodo', 'Espressivo', 'Grazioso', 'Gustoso', 'Maestoso', 'Minueto', 'Moderato', 'Marcía',
                      'Amoroso']
    moderate = moderate_basis + [w[:-1] + t for w in moderate_basis for t in possible_terminations]
    fast_basis = ['Agitato', 'Allegro', 'Con brio', 'Spiritoso', 'Fiero', 'Presto', 'Risoluto', 'Vivace']
    fast = fast_basis + [w[:-1] + t for w in fast_basis for t in possible_terminations]

    if TempoGrouped1 in ['A tempo', 'Giusto']:
        return 'nd'
    elif TempoGrouped1 in slow:
        return 'Slow'
    elif TempoGrouped1 in moderate:
        return 'Moderate'
    elif TempoGrouped1 in fast:
        return 'Fast'

