import re
from typing import List

from music21 import pitch, scale

from musif.common.translate import translate_word
from musif.logs import pwarn

def get_musescore_Instrumentname_And_Family(i, instrument_familiy, p):
    i_name = re.sub('\W+', ' ', i.instrumentName)
    name = translate_word(i_name)
    family = instrument_familiy[name]
    return name, family


def sort(list_to_sort: List[str], reference_list: List[str]) -> List[str]:
    """
    Function that sorts the first list based on the second one
    """
    # TODO: would it be better using numpy?
    indexes = []
    others = []
    for i in list_to_sort:
        # this may be very slow (it contains a full for)
        if i in reference_list:
            # again, the following is another full for
            indexes.append(reference_list.index(i))  # an error indicates that the elements are not present in the main_list; please get in touch with us if so.
            # TODO: throw an exception with this message and give some info on how to solve it (at least)
        else:
            others.append(i)

    indexes = sorted(indexes)
    list_sorted = [reference_list[i] for i in indexes]
    if others:
        pwarn('Some elements of the list were not present in the reference list so they will be placed at the end.')
    return list_sorted + others


def get_gender(character: str) -> str:
    """
    Returns characters' gender for Metastasio's operas according to name.
    """
    if character in ['Didone', 'Selene', 'Dircea', 'Creusa', 'Semira', 'Mandane']:
        return 'Female'
    else:
        return 'Male'


def get_role(character: str) -> str:
    """
    Returns general role type for specific operatic characters. (Metastasio's operas)
    
    """
    if character in ['Demofoonte', 'Licomede', 'Tito', 'Catone', 'Fenicio']:
        return 'Senior ruler'
    elif character in ['Didone', 'Dircea', 'Cleofide', 'Mandane', 'Deidamia', 'Sabina', 'Vitellia', 'Marzia', 'Cleonice']:
        return 'Female lover 1'
    elif character in ['Enea', 'Poro', 'Arbace', 'Timante', 'Achille', 'Adriano', 'Sesto', 'Cesare', 'Alceste', 'Demetrio']:
        return 'Male lover 1'
    elif character in ['Selene', 'Creusa', 'Erissena', 'Semira', 'Emirena', 'Servila', 'Emilia', 'Barsene']:
        return 'Female lover 2'
    elif character in ['Iarba', 'Alessandro', 'Artaserse', 'Cherinto', 'Teagene', 'Farnaspe', 'Annio', 'Olinte']:
        return 'Male lover 2'
    elif character in ['Gandarte', 'Aquilio', 'Fulvio']:
        return 'Male lover 3'
    elif character in ['Araspe', 'Megabise', 'Adrasto', 'Arcade', 'Publio', 'Mitrano']:
        return 'Confidant'
    elif character in ['Osmida', 'Timagene', 'Artabano', 'Matusio', 'Ulisse', 'Osroa']:
        return 'Antagonist'


def get_note_degree(key, note) -> str:
    """
    Function created to obtain the scale degree of a note in a given key
    """
    if 'major' in key:
        scl = scale.MajorScale(key.split(' ')[0])
    else:
        scl = scale.MinorScale(key.split(' ')[0])

    degree = scl.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch(note))
    accidental = degree[1].fullName if degree[1] is not None else ''

    acc = ''
    if accidental == 'sharp':
        acc = '#'
    elif accidental == 'flat':
        acc = 'b'
    elif accidental == 'double-sharp':
        acc = 'x'
    elif accidental == 'double-flat':
        acc = 'bb'

    return acc + str(degree[0])

def get_localTonalty(globalkey: str, degree: str) -> str:
    """
    Obtains local key of a note degree 
    """
    accidental = ''
    if '#' in degree:
        accidental = '#'
        degree = degree.replace('#', '')
    elif 'b' in degree:
        accidental = '-'
        degree = degree.replace('b', '')

    degree_int = roman.fromRoman(degree.upper())

    if 'major' in globalkey:
        pitch_scale = scale.MajorScale(globalkey.split(' ')[0]).pitchFromDegree(degree_int).name
    else:
        pitch_scale = scale.MinorScale(globalkey.split(' ')[0]).pitchFromDegree(degree_int).name

    modulation = pitch_scale + accidental

    # remove flats and sharps
    while '-' in modulation and '#' in modulation:
        modulation = modulation.replace('#', '', 1)
        modulation = modulation.replace('-', '', 1)

    return modulation + ' major' if degree.isupper() else modulation + ' minor'
