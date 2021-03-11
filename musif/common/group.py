##################################################################################
# This file contains the functions to create the groupings for their general
# analysis (A column in reports)
##################################################################################
import re
from collections import OrderedDict

import roman
from music21 import pitch, scale, text

from musif.config import family_to_abbreviation, sound_to_abbreviation, sound_to_family
from musif.common.translate import translate_word


def get_musescoreInstrument_nameAndFamily(i, instrument_familiy, p):
    i_name = re.sub('\W+', ' ', i.instrumentName)
    name = translate_word(i_name)
    # name = exceptions_instrument_parsing(name, p)
    family = instrument_familiy[name]
    return name, family

def sort(list_to_sort, main_list):
    """
    Function that sorts the first list based on the second one
    """
    indexes = []
    huerfanos = []
    for i in list_to_sort:
        if i in main_list:
            indexes.append(main_list.index(i))  # an error indicates that the elements are not present in the main_list; please get in touch with us if so.
        else:
            huerfanos.append(i)

    indexes = sorted(indexes)
    list_sorted = [main_list[i] for i in indexes]
    return list_sorted + huerfanos



def get_TimeSignatureType(timesignature):
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


def get_gender(character):
    # returns characters' gender; for our arias only
    if character in ['Didone', 'Selene', 'Dircea', 'Creusa', 'Semira', 'Mandane']:
        return 'female'
    else:
        return 'male'


def get_role(character):
    # returns general role type for specific operatic characters (for our arias only)
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


def get_note_degree(key, note):
    """
    Function created to obtain the scale degree of a note in a given key #
    """
    if 'major' in key:
        scl = scale.MajorScale(key.split(' ')[0])
    else:
        scl = scale.MinorScale(key.split(' ')[0])

    degree = scl.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch(note))
    accidental = degree[1].fullName if degree[1] != None else ''

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

def get_localTonalty(globalkey, degree):
    """
    Function created to obtain the local key of a note degree #
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

    # neutralize
    while '-' in modulation and '#' in modulation:
        modulation = modulation.replace('#', '', 1)
        modulation = modulation.replace('-', '', 1)

    return modulation + ' major' if degree.isupper() else modulation + ' minor'
