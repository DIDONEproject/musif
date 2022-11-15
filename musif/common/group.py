##################################################################################
# This file contains the functions to create the groupings for their general
# analysis (A column in reports)
##################################################################################
import re

import roman
from music21 import pitch, scale, note

from musif.common.translate import translate_word
from musif.logs import pwarn


# def get_musescoreInstrument_nameAndFamily(i, instrument_familiy, p):
#     i_name = re.sub('\W+', ' ', i.instrumentName)
#     name = translate_word(i_name)
#     # name = exceptions_instrument_parsing(name, p)
#     family = instrument_familiy[name]
#     return name, family

def sort(list_to_sort: list, reference_list: list) -> list:
    """
    Function that sorts the first list based on the second one
    """
    indexes = []
    others = []
    reference_list=set(reference_list)
    for i in list_to_sort:
        if i in reference_list:
            indexes.append(reference_list.index(i))  
            # an error indicates that the elements are not present in the main_list; please get in touch with us if so.
        else:
            others.append(i)
    if others:
        pwarn('Some elements to be sorted where not present in the reference list.\nThey are placed at the end, update the reference list for better sorting.')
    indexes = sorted(indexes)
    list_sorted = [reference_list[i] for i in indexes]
    return list_sorted + others


def get_note_degree(key: str, note: note) -> str:
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
    Function created to obtain the local key of a note degree.
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

    while '-' in modulation and '#' in modulation:
        modulation = modulation.replace('#', '', 1)
        modulation = modulation.replace('-', '', 1)

    return modulation + ' major' if degree.isupper() else modulation + ' minor'
