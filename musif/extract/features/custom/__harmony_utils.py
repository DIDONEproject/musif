import itertools
import re
from collections import Counter
from urllib.request import urlopen

import numpy as np
import pandas as pd
from ms3.expand_dcml import features2type
from pandas.core.frame import DataFrame


REGEX = {}

####################
# METRICAL ANALYSIS
####################    

def get_measures_per_possibility(possibilities, measures, possibilities_list, beats, time_signatures):
    # possibilities=list(set(possibilities))
    voice_measures = {p: 0 for p in possibilities}
    last_voice = 0
    done = 0
    starting_measure = 0
    numberofmeasures = len(measures)
    for i, v in enumerate(possibilities_list):
        if v != last_voice and i < numberofmeasures:
            #no_beats = relationship_timesignature_beats[time_signatures[i - 1]]
            n_beats = get_beatspertsig(time_signatures[i - 1])
            if last_voice in voice_measures :
                num_measures, done = compute_number_of_compasses(done, starting_measure, measures[i - 1], measures[i], beats[i - 1], n_beats)
                voice_measures[last_voice] += num_measures
            last_voice = v
            starting_measure = measures[i] - 1
    
    #último!
    num_measures, _ = compute_number_of_compasses(done, starting_measure, measures[numberofmeasures - 1], measures[numberofmeasures - 1] + 1, beats[numberofmeasures - 1], n_beats)
    voice_measures[last_voice] += num_measures

    #TODO: comprobar que tiene sentido:
    # if (compases[0] != 0 and round(sum(list(compases_voz.values()))) != compases[i]) or (compases[0] == 0 and round(sum(list(compases_voz.values()))) != compases[i] + 1):
    #    print('Error en el recuento de compases de cada sección/voz en get_compases_per_possibility')

    return voice_measures

###########################################################################
# Function that returns the number of beats depending on the time signature
# 6/8 time signature is classified as having two beats; 6/2, 6/4 and 6/16 time signatures
# as having 3 beats.
###########################################################################
def get_beatspertsig(tsig):
    if tsig in ['1/2', '1/4', '1/8', '1/16']:
        return 1
    elif tsig in ['2/2', '2/4', '2/8', '2/16', '6/8']:
        return 2
    elif tsig in ['3/2', '3/4', '3/8', '3/16', '6/2', '6/4', '6/16', '9/2', '9/4', '9/8', '9/16']:
        return 3
    elif tsig in ['4/4','C','4/2','4/8','4/16','8/2','8/4','8/8','8/16', '12/2', '12/4', '12/8', '12/16']:
        return 4
    elif tsig in ['5/2', '5/4', '5/8', '5/16', '10/2', '10/4', '10/8', '10/16']:
        return 5
    elif tsig in ['6/2', '6/4', '6/16']:
        return 6
    elif tsig in ['7/2', '7/4', '7/8', '7/16']:
        return 7
    else:
        return 1


def compute_number_of_compasses(done, starting_measure, end_measure, next_end_measure, current_beat, max_beats):
    starting_measure += done
    if next_end_measure == end_measure:
        #hacer el cálculo concreto con el número de beats
        measures = end_measure - 1 - starting_measure
        # habrá que sumarle current_beat / max_beats. Antes convertir current_beat en numérico
        if type(current_beat) == str:
            numbers = current_beat.split('.')
            first = int(numbers[0])
            second = numbers[1].split('/')
            second = int(second[0]) / int(second[1])
            current_beat = first + second

        return measures + (current_beat / max_beats), (current_beat / max_beats)
    else:
        if next_end_measure - end_measure > 1:
            return end_measure - starting_measure + (next_end_measure - 1 - end_measure), 0
        else:
            return end_measure - starting_measure, 0

#########################################################################
# Como sections tiene una indicación por compás, pero a lo largo del script
# trabajamos con la tabla harmonic_analysis, que tiene tantas entradas por 
# compás como anotaciones harmónicas, repetimos las secciones según el número

def continued_sections(sections, mc):
    extended_sections = []
    repeated_measures = Counter(mc)
    for i, c in enumerate(repeated_measures):
        extended_sections.append([sections[i]] * repeated_measures[c])

    # Flat list
    return list(itertools.chain(*extended_sections))

####################
# LOCAL KEY
####################

################################################################################
# Function to return the harmonic function1 based on the global key mode. Uppercase if
# mode is major, lowercase if minor. 2nd, 4th, adn 6th degrees are considered 
# as classes of subdominant function. In major mode, vi is treatred as the relative key (rm);
# in the minor, III = relative major (rj).
# Lowered degrees are indicated with 'b', raised with '#' (bII = Neapolitan key).
# Leading notes are abrreviated as LN.

# def get_localkey_1(localkey, mode):
#     if localkey in ['VII']:
#             return 'LN'
#     elif localkey in ['#VII']:
#         return '#LN'
#     elif localkey in ['#vii']:
#         return '#ln'

#     localkey=localkey.replace('b','-')

#     #TODO: mirar bemol napolitano

#     reference={'T':['i'], 'D':['v'], 'SD': ['ii', 'iv', 'vi'], 'M': ['iii']
#     }
#     for key, value in reference.items():
#         if localkey.replace('#','').replace('-','').lower() in value:
#             output=key.lower() if localkey.islower() else key
#             if '-' in localkey:
#                 output='-'+ output
#             elif '#' in localkey:
#                 output='#'+ output
#             return output.replace('-','b')
#     if mode == 'M':
#         # elements specific of the major mode
#         if localkey=='vii':
#             return 'D'
#         elif  localkey == '#vii':
#             return '#ln'
#         elif localkey=='bVII':
#             return 'ST'
#         elif localkey=='bvii':
#             return 'st'
#         elif  localkey== 'VII':
#             return '#ST'
#         else:
#             print(localkey, 'not available')
#     else:
#         # localkeys specific of the minor mode
#         if localkey=='#vii':
#             return 'D'
#         elif  localkey == 'VII':
#             return 'ST'
#         elif  localkey=='bVII':
#             return 'bST'
#         elif  localkey=='bvii':
#             return 'bst'
#         elif  localkey=='#VII':
#             return 'LN'
#         elif localkey=='vii':
#             return 'st'
#         else:
#             print(localkey, ' is not available!')

#############################################################
# Function to return function2 based on function1. It
# disregards the mode. #
# def get_localkey_2(chord):
#     chord=chord.replace('b','-') #to be able to convert to upper without affecting flats
    
#     if chord in ['rm', 'rj']:
#         return 'rel'
#     elif chord.upper() in ['ST', 'LN']:
#         return 'ST'
#     else:
#         return chord.upper().replace('-','b')

# Function to return harmonic functions (1 and 2) based on a list of keys #
def get_keys(list_keys, mode):
    result_dict = {t: get_degree_1(t, mode) for t in set(list_keys)}
    # result_dict = {t: get_localkey_1(t, mode) for t in set(list_keys)}
    function1 = [result_dict[t] for t in list_keys]
    function2 = [get_degree_2(g1) for g1 in function1]
    # function2 = [get_localkey_2(g1) for g1 in function1]
    return function1, function2

###################
# KEYAREAS
###################

def get_keyareas_lists(keys, g1, g2):
    # key areas
    key_areas = []
    key_areas_g1 = []
    key_areas_g2 = []
    last_key = ''
    for i, k in enumerate(keys):
        if k != last_key:
            key_areas.append(k)
            key_areas_g1.append(g1[i])
            key_areas_g2.append(g2[i])
            last_key = k
    return key_areas, key_areas_g1, key_areas_g2

def get_keyareas(lausanne_table, major = True):
    # indexes_A = [i for i, s in enumerate(sections) if s == "A"]
    # indexes_B = [i for i, s in enumerate(sections) if s == "B"]

    """possible_keys = harmonic_analysis.Chords.dropna().tolist()
    grouping1 = harmonic_analysis['GC1M' if major else 'GC1m'].dropna().tolist()
    grouping2 = harmonic_analysis['GC2M' if major else 'GC2m'].dropna().tolist()
    
    g1 = [grouping1[possible_keys.index(c)] for c in keys]
    g2 = [grouping2[possible_keys.index(c)] for c in keys]"""

    keys = lausanne_table.localkey.dropna().tolist()
    g1, g2 = get_keys(keys, 'M' if major else 'm')

    key_areas, key_areas_g1, key_areas_g2 = get_keyareas_lists(keys, g1, g2)
    counter_keys = Counter(key_areas)
    counter_grouping1 = Counter(key_areas_g1)
    counter_grouping2 = Counter(key_areas_g2)
    
    # A_Keys = [keys[i] for i in indexes_A]
    # g1_A = [g1[i] for i in indexes_A]
    # g2_A = [g2[i] for i in indexes_A]
    # key_area_A, key_areas_g1_A, key_areas_g2_A = get_keyareas_lists(A_Keys, g1_A, g2_A)
    # counter_keys_A = Counter(key_area_A)
    # counter_grouping1_A  = Counter(key_areas_g1_A)
    # counter_grouping2_A  = Counter(key_areas_g2_A)
    
    # B_Keys = [keys[i] for i in indexes_B]
    # g1_B = [g1[i] for i in indexes_B]
    # # g2_B = [g2[i] for i in indexes_B]
    # key_areas_B, key_areas_g1_B, key_areas_g2_B = get_keyareas_lists(B_Keys, g1_B, g2_B)
    # counter_keys_B = Counter(key_areas_B)
    # counter_grouping1_B  = Counter(key_areas_g1_B)
    # counter_grouping2_B  = Counter(key_areas_g2_B)

    #Keys based on the number of measures
    measures = lausanne_table.mc.dropna().tolist()
    beats = lausanne_table.mc_onset.dropna().tolist()
    time_signatures = lausanne_table.timesig.tolist()
    """xml_ts = harmonic_analysis['TimeSignature'].dropna().tolist()
    xml_beats = harmonic_analysis['NoBeats'].dropna().tolist()
    relationship_timesignature_beats = {ts: xml_beats[i] for i, ts in enumerate(xml_ts)}"""
    key_compasses = get_measures_per_possibility(list(set(keys)), measures, keys, beats, time_signatures)
    total_compasses = sum(list(key_compasses.values()))
    key_compasses = {kc:key_compasses[kc]/total_compasses for kc in key_compasses}
    keyGrouping1_compasses = get_measures_per_possibility(list(set(g1)), measures, g1, beats, time_signatures)
    keyGrouping1_compasses = {kc:keyGrouping1_compasses[kc]/sum(list(keyGrouping1_compasses.values())) for kc in keyGrouping1_compasses}
    keyGrouping2_compasses = get_measures_per_possibility(list(set(g2)), measures, g2, beats, time_signatures)
    keyGrouping2_compasses = {kc:keyGrouping2_compasses[kc]/sum(list(keyGrouping2_compasses.values())) for kc in keyGrouping2_compasses}
    # SECTION A
    # measures_A = [measures[i] for i in indexes_A]
    # beats_A = [beats[i] for i in indexes_A]
    # time_signatures_A = [time_signatures[i] for i in indexes_A]
    # key_compasses_A = get_compases_per_possibility(list(set(A_Keys)), measures_A, A_Keys, beats_A, time_signatures_A)
    # total_compasses_A = sum(list(key_compasses_A.values()))
    # key_compasses_A = {kc:key_compasses_A[kc]/total_compasses_A for kc in key_compasses_A}
    # keyGrouping1_compasses_A = get_compases_per_possibility(list(set(g1_A)), measures_A, g1_A, beats_A, time_signatures_A)
    # keyGrouping1_compasses_A = {kc:keyGrouping1_compasses_A[kc]/sum(list(keyGrouping1_compasses_A.values())) for kc in keyGrouping1_compasses_A}
    # keyGgrouping2_compasses_A = get_compases_per_possibility(list(set(g2_A)), measures_A, g2_A, beats_A, time_signatures_A)
    # keyGgrouping2_compasses_A = {kc:keyGgrouping2_compasses_A[kc]/sum(list(keyGgrouping2_compasses_A.values())) for kc in keyGgrouping2_compasses_A}
    # # SECTION B
    # measures_B = [measures[i] for i in indexes_B]
    # beats_B = [beats[i] for i in indexes_B]
    # time_signatures_B = [time_signatures[i] for i in indexes_B]
    # key_compasses_B = get_compases_per_possibility(list(set(B_Keys)), measures_B, B_Keys, beats_B, time_signatures_B)
    # total_compasses_B = sum(list(key_compasses_B.values()))
    # key_compasses_B = {kc:key_compasses_B[kc]/total_compasses_B for kc in key_compasses_B}
    # keyGrouping1_compasses_B = get_compases_per_possibility(list(set(g1_B)), measures_B, g1_B, beats_B, time_signatures_B)
    # keyGrouping1_compasses_B = {kc:keyGrouping1_compasses_B[kc]/sum(list(keyGrouping1_compasses_B.values())) for kc in keyGrouping1_compasses_B}
    # keyGgrouping2_compasses_B = get_compases_per_possibility(list(set(g2_B)), measures_B, g2_B, beats_B, time_signatures_B)
    # keyGgrouping2_compasses_B = {kc:keyGgrouping2_compasses_B[kc]/sum(list(keyGgrouping2_compasses_B.values())) for kc in keyGgrouping2_compasses_B}

    # final dictionary
    keyareas = {'TotalNumberKeyAreas': len(counter_keys)}
    total_key_areas = sum(counter_keys.values())
    total_g1_areas = sum(counter_grouping1.values())
    total_g2_areas = sum(counter_grouping2.values())
    # total_key_areas_A = sum(counter_keys_A.values())
    # total_g1_areas_A = sum(counter_grouping1_A.values())
    # total_g2_areas_A = sum(counter_grouping2_A.values())
    # total_key_areas_B = sum(counter_keys_B.values())
    # total_g1_areas_B = sum(counter_grouping1_B.values())
    # total_g2_areas_B = sum(counter_grouping2_B.values())

    for ck in counter_keys:
        keyareas['Key'+ck] = counter_keys[ck]
        keyareas['KeyCompasses'+ck] = key_compasses[ck]
        keyareas['KeyModulatory'+ck] = counter_keys[ck]/total_key_areas
        keyareas['KeyModComp'+ck] = (keyareas['KeyCompasses'+ck] + keyareas['KeyModulatory'+ck]) / 2
    for cg in counter_grouping1:
        keyareas['KeyGrouping1'+cg] = counter_grouping1[cg]
        keyareas['KeyGrouping1Compasses'+cg] = keyGrouping1_compasses[cg]
        keyareas['KeyGrouping1Modulatory'+cg] = counter_grouping1[cg]/total_g1_areas
        keyareas['KeyGrouping1ModComp'+cg] = (keyareas['KeyGrouping1Compasses'+cg] + keyareas['KeyGrouping1Modulatory'+cg]) / 2
    for cg in counter_grouping2:
        keyareas['KeyGrouping2'+cg] = counter_grouping2[cg]
        keyareas['KeyGrouping2Compasses'+cg] = keyGrouping2_compasses[cg]
        keyareas['KeyGrouping2Modulatory'+cg] = counter_grouping2[cg]/total_g2_areas
        keyareas['KeyGrouping2ModComp'+cg] = (keyareas['KeyGrouping2Compasses'+cg] + keyareas['KeyGrouping2Modulatory'+cg]) / 2

    # for ck in counter_keys_A:
    #     keyareas['KeySectionA'+ck] = counter_keys_A[ck]
    #     keyareas['KeyModCompSectionA'+ck] = (key_compasses_A[ck] + (counter_keys_A[ck]/total_key_areas_A)) / 2
    # for cg in counter_grouping1_A:
    #     keyareas['KeyGgrouping1SectionA'+cg] = counter_grouping1_A[cg]
    #     keyareas['KeyGgrouping1ModCompSectionA'+cg] = (keyGrouping1_compasses_A[cg] + (counter_grouping1_A[cg]/total_g1_areas_A)) / 2
    # for cg in counter_grouping2_A:
    #     keyareas['KeyGgrouping2SectionA'+cg] = counter_grouping2_A[cg]
    #     keyareas['KeyGgrouping2ModCompSectionA'+cg] = (keyGgrouping2_compasses_A[cg] + (counter_grouping2_A[cg]/total_g2_areas_A)) / 2
    
    # for ck in counter_keys_B:
    #     keyareas['KeySectionB'+ck] = counter_keys_B[ck]
    #     keyareas['KeyModCompSectionB'+ck] = (key_compasses_B[ck] + (counter_keys_B[ck]/total_key_areas_B)) / 2
    # for cg in counter_grouping1_B:
    #     keyareas['KeyGgrouping1SectionB'+cg] = counter_grouping1_B[cg]
    #     keyareas['KeyGgrouping1ModCompSectionB'+cg] = (keyGrouping1_compasses_B[cg] + (counter_grouping1_B[cg]/total_g1_areas_B)) / 2
    # for cg in counter_grouping2_B:
    #     keyareas['KeyGgrouping2SectionB'+cg] = counter_grouping2_B[cg]
    #     keyareas['KeyGgrouping2ModCompSectionB'+cg] = (keyGgrouping2_compasses_B[cg] + (counter_grouping2_B[cg]/total_g2_areas_B)) / 2

    return keyareas

# ####################
# DEGREES (for relative roots, numerals and chords)
####################

###########################################################################
# Function to obtain the harmonic function1 of every relativeroot, chord, or numeral#
# harmonic_analysis: columnas AG-AK
###########################################################################
def get_degree_1(element, mode):
    if element.lower()=='bii':
        return 'NAP'
    #It6/V -> viio(-3)
    # '-' represents flats
    element=element.replace('b','-')
    
    reference={'T':['i'], 'D':['v', 'vii'], 'SD': ['ii', 'iv', 'vi'], 'M': ['iii']
    }
    for key, value in reference.items():
        if element.replace('#','').replace('-','').lower() in value:
            output=key.lower() if element.islower() else key
            if '-' in element:
                output='-'+ output
            elif '#' in element:
                output='#'+ output
            return output.replace('-','b')
    
    #Check spetial chords

    if any([i for i in ('It','Ger', 'Fr') if i in element]):
        return 'V'

    if mode == 'M':
        if element=='vii':
            return 'D'
        elif  element == '#vii':
            return '#ln'
        elif element=='bVII':
            return 'ST'
        elif element=='bvii':
            return 'st'
        elif  element== 'VII':
            return 'LN'
        else:
            print(f'Element: {element} not available')
    else:
        if element=='#vii':
            return 'D'
        elif  element == 'VII':
            return 'ST'
        elif  element=='bVII':
            return 'bST'
        elif  element=='bvii':
            return 'bst'
        elif  element=='#VII':
            return 'LN'
        elif element=='vii':
            return 'st'
        else:
            print(element, ' is not available!')
    return ''

###########################################################################
# Function to obtain the harmonic function2 of every relativeroot, chord, or numeral.
###########################################################################
def get_degree_2(element):
    element=element.replace('b','-') #to be able to convert to CAPS without affecting flats
    if element.lower() == '#ln':
        return '#ST'
    elif element in ['rm', 'rj']:
        return 'rel'
    elif element.upper() in ['ST', 'LN']:
        return 'ST'
    else:
        return element.upper().replace('-','b')

####################
# NUMERALS
####################

def get_numeral_1(numeral, relativeroot, local_key):
    # We use relative root column to discriminate if there is a relatuive numeral or not
    if str(relativeroot) != 'nan':
        return get_degree_1(numeral, 'M' if relativeroot.isupper() else 'm')
    else:
        return get_degree_1(numeral, 'M' if local_key.isupper() else 'm')

def get_numerals_lists(list_numerals, list_relativeroots, list_local_keys):
    tuples = list(zip(list_numerals, list_relativeroots, list_local_keys))
    result_dict = {t: get_numeral_1(*t) for t in set(tuples)}
    function1 = [result_dict[t] for t in tuples]
    function2 = [get_degree_2(g1) for g1 in function1]
    return function1, function2

####################
# CHORDS
####################

def get_chord_types(lausanne_table):
    # form = lausanne_table.form.tolist()
    # #los que son nan hay que cambiarlos en función de una serie de reglas
    # figbass = lausanne_table.figbass.tolist()
    # numerals = lausanne_table.numeral.tolist()
    form_l = make_type_col(lausanne_table)
        
    #convert the list of forms in their groups
    grouped_forms = get_chordtypes(form_l)

    form_counter = Counter(grouped_forms)
    features_chords= {}
    for f in form_counter:
        features_chords['chords_' + str(f)] = form_counter[f] / sum(list(form_counter.values()))
    return features_chords

def get_chords(lausanne_table):
    relativeroots = lausanne_table.relativeroot.tolist()

    keys = lausanne_table.localkey.dropna().tolist() 

    # Coger columna numeral que hace una pre-separción ?()?)?)

    chords = lausanne_table.chord.dropna().tolist()
    # chords = lausanne_table.numeral.dropna().tolist()

    chords_functionalities1, chords_functionalities2 = get_chords_functions(chords, relativeroots, keys)

    chords_numbers = Counter(chords)
    chords_functionalities1 = Counter(chords_functionalities1)
    chords_functionalities2 = Counter(chords_functionalities2)

    total_chords=sum(Counter(chords).values())
    
    #chords
    chords = {}
    for degree in chords_numbers:
        chords['chords_'+degree] = chords_numbers[degree]/total_chords

    #chords group 1
    chords_g1 = {}
    total_chords_g1=sum(Counter(chords_functionalities1).values())

    for degree in chords_functionalities1:
        chords_g1['chords_Grouping1'+ degree] = chords_functionalities1[degree]/total_chords_g1
    
    #chords group 2
    chords_group2 = {}
    total_chords_g2=sum(Counter(chords_functionalities2).values())

    for degree in chords_functionalities2:
        chords_group2['chords_Grouping2' + degree] = chords_functionalities2[degree]/total_chords_g2
    return chords, chords_g1, chords_group2

#################################################################
# This function takes the first characters in the chord to 
# obtain its grouping
def parse_chord(first_char):
    if '(' in first_char:
        first_char = first_char.split('(')[0]
    if 'o' in first_char:
        first_char = first_char.split('o')[0]
    if '+' in first_char:
        first_char = first_char.split('+')[0]
    if '%' in first_char:
        first_char = first_char.split('%')[0]
    if 'M' in first_char:
        first_char = first_char.split('M')[0]
        
    # look for a number
    chars = []
    for character in first_char:
        if not character.isdigit():
            chars.append(character)
        else:
            break

    return ''.join(chars)

####################
# CHORD FORM
####################

#############################################
# Function that returns the chord_type grouping
def get_chordtype(chord_type):
    chord_type=str(chord_type)
    if chord_type.lower()=='m':
        return 'triad'
    elif chord_type in ['7', 'mm7', 'Mm7', 'MM7', 'mM7']:
        return '7th'
    elif chord_type in ['o', 'o7', '%', '%7']:
        return 'dim'
    elif chord_type in ['+', '+M7', '+m7']:
        return 'aug'
    elif chord_type == 'nan':
        return 'nan'
    else:
        print("Chord type ", str(chord_type), 'not observed')
        return ''

#############################################
# Function that returns the chord_type grouping

def get_chordtypes(chordtype_list):
    return [get_chordtype(chord_type) for chord_type in chordtype_list]

#############################################
# Function to return the first grouping for any chord
# in any given local key.
def get_chord_1(chord, local_key):

    #persegui It6/V. Coger columna numeral paraparsear acordes

    mode = 'M' if local_key else 'm'
    if '/' not in chord:
        return get_degree_1(parse_chord(chord), mode)
    else: 
        parts = chord.split('/')
        degree = get_degree_1(parse_chord(parts[0]), 'M' if parts[1].isupper() else 'm')
        if len(parts) == 2:
            chord = get_degree_1(parts[1], mode)
            return '/'.join([degree, chord])
        elif len(parts) == 3:
            chord1 = get_degree_1(parts[1], 'M' if parts[2].isupper() else 'm')
            chord2 = get_degree_1(parts[2], mode)
            return '/'.join([degree, chord1, chord2])

# Function to return the second grouping for any chord in any given local key,
def get_chord_2(grouping1, relativeroot, local_key):
    mode = 'M' if local_key else 'm'
    if str(relativeroot) != 'nan':
        mode = 'M' if relativeroot.isupper() else 'm'
    parts = grouping1.split('/')
    degree = get_degree_2(parts[0])
    if len(parts) == 2:
        chords = get_degree_2(parts[1])
        return '/'.join([degree, chords])
    elif len(parts) == 3:
        # chord_1 = get_degree_2(parts[1], 'M' if parts[2].isupper() else 'm')
        chord_1 = get_degree_2(parts[1])
        chord_2 = get_degree_2(parts[2])
        return '/'.join([degree, chord_1, chord_2])
    return degree

def get_chords_functions(list_chords, list_relativeroots, list_local_keys):

    #TODO: review that the order is not changed.

    chords_localkeys = list(zip(list_chords, list_local_keys))
    functionalities_dict = {t: get_chord_1(*t) for t in set(chords_localkeys)}
    function_1 = [functionalities_dict[t] for t in chords_localkeys]
    chords_localkeys = list(zip(function_1, list_relativeroots, list_local_keys))
    function_2 = [get_chord_2(*g1) for g1 in chords_localkeys]
    return function_1, function_2

# ### MODULATIONS ###
# def get_modulations(lausanne_table: DataFrame, sections, major = True):
#     keys = lausanne_table.localkey.dropna().tolist()
#     grouping, _ = get_keys_functions(keys, mode = 'M' if major else 'm')
#     modulations_sections = {g:[] for g in grouping}

#     # Count the number of sections in each key
#     last_key = ''
#     for i, k in enumerate(keys):
#         if (k.lower() != 'i') and k != last_key: #premisa
#             # section = sections[i] #??? NON comprendo
#             last_key = k
#             modulation = grouping[i]
#             # modulations_sections[modulation].append(section)
#         # if last_key == k and sections[i] != section:
#         #     section = sections[i]
#         #     modulations_sections[modulation].append(section)
    
#     #borramos las modulaciones con listas vacías y dejamos un counter en vez de una lista
#     ms = {}
#     # for m in modulations_sections:
#     #     if len(modulations_sections[m]) != 0:
#     #         ms['Modulations'+str(m)] = len(list(set(modulations_sections[m])))
#     # return ms


def make_type_col(df, num_col='numeral', form_col='form', fig_col='figbass'):
    """ Create a new Series with the chord type for every row of `df`.
        Uses: features2type()
    """
    param_tuples = list(df[[num_col, form_col, fig_col]].itertuples(index=False, name=None))
    result_dict = {t: features2type(*t) for t in set(param_tuples)}
    return pd.Series([result_dict[t] for t in param_tuples], index=df.index, name='chordtype')



def sort_labels(labels, git_branch='master', drop_duplicates=True, verbose=True, **kwargs):
    """ Sort a list of DCML labels following custom criteria.
        Uses: split_labels()
    Parameters
    ----------
    labels : :obj:`collection` or :obj:`pandas.Series`
        The labels you want to sort.
    git_branch : :obj:`str`, optional
        The branch of the DCMLab/standards repo from which you want to use the regEx.
    drop_duplicates : :obj:`bool`, optional
        By default, the function returns an ordered list of unique labels. Set to
        False in order to keep duplicate labels. Note that where the ordered features
        are identical, labels appear in the order of their occurrence.
    verbose : .obj:`bool`, optional
        By default, values that are missing from custom orderings are printed out.
        Pass False to prevent that.
    kwargs : {'values', 'occurrences', 'rvalues', 'roccurrences'}, :obj:`dict`, :obj:`list` or callable
        Pass one argument for every feature that you want to sort in the order
        in which features should be used for sorting. The arguments will be mapped
        on the respective columns which should yield alpha-numeric values to be sorted.
        globalkey
        localkey
        pedal
        chord
        numeral
        form
        figbass
        changes
        relativeroot
        pedalend
        phraseend
        chordtype
    Examples
    --------
    .. highlight:: python
        # Sort numerals by occurrences (descending), the figbass by occurrences (ascending), and
        # the form column by the given order
        sort_labels(labels, numeral='occurrences', figbass='roccurrences', form=['', '+', 'o', '%', 'M'])
        # Sort numerals by custom ordering and each numeral by the (globally) most frequent chord types.
        sort_labels(labels, numeral=['I', 'V', 'IV'], chordtype='occurrences')
        # Sort relativeroots alphabetically and the numerals by a custom ordering which
        # is equivalent to ['V', 'vii', '#vii']
        sort_labels(labels, relativeroot='rvalues', numeral={'vii': 5, 'V': 0,  '#vii': 10})
        # Sort chord types by occurrences starting with the least frequent and sort their inversions
        # following the given custom order
        sort_labels(labels, chordtype='roccurrences', figbass=['2', '43', '65', '7'])
    """
    if len(kwargs) == 0:
        raise ValueError("Pass at least one keyword argument for sorting...")
    if not isinstance(labels, pd.core.series.Series):
        if isinstance(labels, pd.core.frame.DataFrame):
            raise TypeError("Pass only one column of your DataFrame.")
        labels = pd.Series(labels)
    if drop_duplicates:
        labels = labels.drop_duplicates()
    features = split_labels(labels, git_branch)

    def make_keys(col, order):

        def make_order_dict(it):
            missing = [v for v in col.unique() if v not in it]
            if len(missing) > 0 and verbose:
                print(f"The following values were missing in the custom ordering for column {col.name}:\n{missing}")
            return {v: i for i, v in enumerate(list(it) + missing)}

        if order in ['values', 'rvalues']:
            keys = sorted(set(col)) if order == 'values' else reversed(sorted(set(col)))
            order_dict = make_order_dict(keys)
        elif order in ['occurrences', 'roccurrences']:
            keys = col.value_counts(dropna=False).index if order == 'occurrences' else col.value_counts(dropna=False, ascending=True).index
            order_dict = make_order_dict(keys)
        elif order.__class__ is not dict:
            try:
                order_dict = make_order_dict(order)
            except:
                # order is expected to be a callable:
                return np.vectorize(order)(col)
        else:
            order_dict = order

        return np.vectorize(order_dict.get)(col)

    if 'chordtype' in kwargs:
        features['chordtype'] = make_type_col(features)
    key_cols = {col: make_keys(features[col], order) for col, order in kwargs.items() if col in features.columns}
    df = pd.DataFrame(key_cols, index=features.index)
    ordered_ix = df.sort_values(by=df.columns.to_list()).index
    return labels.loc[ordered_ix]

    
def split_labels(labels, git_branch='master', dropna=True):
    """ Split DCML harmony labels into their respective features using the regEx
        from the indicated branch of the DCMLab/standards repository.
    Parameters
    ----------
    labels : :obj:`pandas.Series`
        Harmony labels to be split.
    git_branch : :obj:`str`, optional
        The branch of the DCMLab/standards repo from which you want to use the regEx.
    dropna : :obj:`bool`, optional
        Drop rows where the regEx didn't match.
    """
    global REGEX
    if git_branch not in REGEX:
        url = f"https://raw.githubusercontent.com/DCMLab/standards/{git_branch}/harmony.py"
        glo, loc = {}, {}
        exec(urlopen(url).read(), glo, loc)
        REGEX[git_branch] = re.compile(loc['regex'], re.VERBOSE)
    regex = REGEX[git_branch]
    cols = ['globalkey', 'localkey', 'pedal', 'chord', 'numeral', 'form', 'figbass', 'changes', 'relativeroot', 'pedalend', 'phraseend']
    res = labels.str.extract(regex, expand=True)[cols]
    if dropna:
        return res.dropna(how='all').fillna('')
    return res.fillna('')
