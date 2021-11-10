import itertools
import re
from collections import Counter

import numpy as np
import pandas as pd
from ms3.expand_dcml import features2type, split_labels

from musif.musicxml.tempo import get_number_of_beats
from .constants import *

# from musif.extract.utils import get_beatspertsig


REGEX={}
####################
# HARMONIC ANALYSIS
####################   

def get_harmonic_rhythm(ms3_table)-> dict:
    hr={}
    measures = ms3_table.mc.dropna().tolist()
    playthrough= ms3_table.playthrough.dropna().tolist()

    measures_compressed=[i for j, i in enumerate(measures) if i != measures[j-1]]
    
    chords = ms3_table.chord.dropna().tolist()
    chords_number=len([i for j, i in enumerate(chords) if i != chords[j-1]])
    # beats = ms3_table.mc_onset.dropna().tolist()
    # voice = ['N' if str(v) == 'nan' else v for v in ms3_table.voice.tolist()]
    time_signatures = ms3_table.timesig.tolist()
    
    harmonic_rhythm = chords_number/len(measures_compressed)

    if len(Counter(time_signatures)) == 1:
        harmonic_rhythm_beats = chords_number/(get_number_of_beats(time_signatures[0])*len(measures_compressed))
    else:
        periods_ts=[]
        time_changes=[]
        for t in range(1, len(time_signatures)):
            if time_signatures[t] != time_signatures[t-1]:
                # what measure in compressed list corresponds to the change in time signature
                time_changes.append(time_signatures[t-1])
                periods_ts.append(len(measures_compressed[0:playthrough[t-1]])-sum(periods_ts))

        # Calculating harmonic rythm according to beats periods
        harmonic_rhythm_beats = chords_number/sum([period * get_number_of_beats(time_changes[j]) for j, period in enumerate(periods_ts)])

    hr[HARMONIC_RHYTHM] = harmonic_rhythm
    hr[HARMONIC_RHYTHM_BEATS] = harmonic_rhythm_beats

    return hr

def get_measures_per_key(keys_options, measures, keys, mc_onsets, time_signatures):
    key_measures = {p: 0 for p in keys_options}
    last_key = 0
    done = 0
    starting_measure = 0

    new_measures = create_measures_extended(measures)
    numberofmeasures = len(new_measures)
           

    for i, key in enumerate(keys):
        if key != last_key and i < numberofmeasures:
            #no_beats = relationship_timesignature_beats[time_signatures[i - 1]]
            n_beats = get_number_of_beats(time_signatures[i - 1])

            if last_key in key_measures :
                # num_measures, done = compute_number_of_measures(done, starting_measure, measures[i - 1], measures[i], mc_onsets[i - 1], n_beats)
                num_measures, done = compute_number_of_measures(done, starting_measure, new_measures[i - 1], new_measures[i], mc_onsets[i - 1], n_beats)
                key_measures[last_key] += num_measures

            last_key = key
            starting_measure = new_measures[i] - 1
    
    #último!
    num_measures, _ = compute_number_of_measures(done, starting_measure, new_measures[numberofmeasures - 1], new_measures[numberofmeasures - 1] + 1, mc_onsets[numberofmeasures - 1], n_beats)

    # num_measures, _ = compute_number_of_measures(done, starting_measure, measures[numberofmeasures - 1], measures[numberofmeasures - 1] + 1, mc_onsets[numberofmeasures - 1], n_beats)
    key_measures[last_key] += num_measures

    try:
        assert not (new_measures[0] != 0 and round(sum(list(key_measures.values()))) != new_measures[i])
        assert not (new_measures[0] == 0 and round(sum(list(key_measures.values()))) != new_measures[i] + 1)
    except AssertionError as e:
        print('There was an error counting the measures!: ', e)
        return {}
    return key_measures

def create_measures_extended(measures):
    new_measures=[]
    new_measures.append(measures[0])
    for i in range(1,len(measures)):
        if measures[i] < max(measures[:i]):
            if same_measure(measures, i):
                new_measures.append(new_measures[i-1])
            else:
                new_measures.append(new_measures[i-1]+1)
        else:
            new_measures.append(measures[i])
    return new_measures

def same_measure(measures, i):
    return measures[i] == measures[i-1]



def compute_number_of_measures(done, starting_measure, previous_measure, measure, current_onset, num_beats):
    starting_measure += done
    if measure == previous_measure: #We are in the same measure, inside of it

        #TODO: hacer el cálculo concreto con el número de beats(?)
        measures = previous_measure - 1 - starting_measure

        # habrá que sumarle current_beat / max_beats. Antes convertir current_beat en numérico
        if type(current_onset) == str:
            numbers = current_onset.split('.')
            first = int(numbers[0])
            second = numbers[1].split('/')
            second = int(second[0]) / int(second[1])
            current_onset = first + second

        return measures + (current_onset / num_beats), (current_onset / num_beats)
    else:
        if measure - previous_measure > 1: #Change occurs in a change of measures
            return previous_measure - starting_measure + (measure - 1 - previous_measure), 0 ###WTF IS DIS
        else:
            return previous_measure - starting_measure, 0

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

# Function to return harmonic functions (1 and 2) based on a list of keys #
def get_keys(list_keys, mode):
    result_dict = {t: get_function_first(t, mode) for t in set(list_keys)}
    # result_dict = {t: get_localkey_1(t, mode) for t in set(list_keys)}
    function1 = [result_dict[t] for t in list_keys]
    function2 = [get_function_second(g1) for g1 in function1]
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

    keys = lausanne_table.localkey.dropna().tolist()
    g1, g2 = get_keys(keys, 'M' if major else 'm')

    key_areas, key_areas_g1, key_areas_g2 = get_keyareas_lists(keys, g1, g2)
    number_blocks_keys = Counter(key_areas)
    number_blocks_grouping1 = Counter(key_areas_g1)
    number_blocks_grouping2 = Counter(key_areas_g2)
    
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

    measures = lausanne_table.mc.dropna().tolist()
    beats = lausanne_table.mc_onset.dropna().tolist()
    time_signatures = lausanne_table.timesig.tolist()

    key_measures = get_measures_per_key(list(set(keys)), measures, keys, beats, time_signatures)

    total_measures = sum(list(key_measures.values()))
    key_measures_percentage = {kc:float(key_measures[kc]/total_measures) for kc in key_measures} #ASI mejor?
    # key_measures = {kc:key_measures[kc]/total_measures for kc in key_measures}
    
    keyGrouping1_measures = get_measures_per_key(list(set(g1)), measures, g1, beats, time_signatures)
    keyGrouping1_measures = {kc:keyGrouping1_measures[kc]/sum(list(keyGrouping1_measures.values())) for kc in keyGrouping1_measures}
    keyGrouping2_measures = get_measures_per_key(list(set(g2)), measures, g2, beats, time_signatures)
    keyGrouping2_measures = {kc:keyGrouping2_measures[kc]/sum(list(keyGrouping2_measures.values())) for kc in keyGrouping2_measures}
    
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

    total_key_areas = sum(number_blocks_keys.values())
    total_g1_areas = sum(number_blocks_grouping1.values())
    total_g2_areas = sum(number_blocks_grouping2.values())
    
    keyareas = {'TotalNumberKeyAreas': total_key_areas, 'TotalNumberMeasures': int(total_measures) }

    # total_key_areas_A = sum(counter_keys_A.values())
    # total_g1_areas_A = sum(counter_grouping1_A.values())
    # total_g2_areas_A = sum(counter_grouping2_A.values())
    # total_key_areas_B = sum(counter_keys_B.values())
    # total_g1_areas_B = sum(counter_grouping1_B.values())
    # total_g2_areas_B = sum(counter_grouping2_B.values())

    for key in number_blocks_keys:
        # keyareas[KEY_prefix + key + '_numberOfblocs'] = number_blocks_keys[key]
        # keyareas[KEY_prefix + KEY_MEASURES + key] = float(key_measures[key])
        keyareas[KEY_prefix + key + KEY_PERCENTAGE ] = float(key_measures_percentage[key]) #procentaje de compases de cada I, i, etc. en el total
        keyareas[KEY_prefix + KEY_MODULATORY + key] = number_blocks_keys[key]/total_key_areas
    
    # for counter_grouping in number_blocks_grouping1:
    #     keyareas[KEY_GROUPING+'1_'+counter_grouping] = number_blocks_grouping1[counter_grouping]
    #     keyareas[KEY_GROUPING+'1_'+ KEY_PERCENTAGE  +counter_grouping] = float(keyGrouping1_measures[counter_grouping])
    #     keyareas[KEY_GROUPING+'1_' + KEY_MEASURES + counter_grouping] =float( keyGrouping1_measures[counter_grouping])
    #     keyareas[KEY_GROUPING+'1_'+KEY_MODULATORY+counter_grouping] = number_blocks_grouping1[counter_grouping]/total_g1_areas
    
    # for counter_grouping in number_blocks_grouping2:
    #     keyareas[KEY_GROUPING+'2_'+counter_grouping] = number_blocks_grouping2[counter_grouping]
    #     keyareas[KEY_GROUPING+'2_'+KEY_PERCENTAGE+counter_grouping] = float(keyGrouping2_measures[counter_grouping])
    #     keyareas[KEY_GROUPING+'2_' + KEY_MEASURES + counter_grouping] = float(keyGrouping2_measures[counter_grouping])
    #     keyareas[KEY_GROUPING+'2_'+KEY_MODULATORY+counter_grouping]  = number_blocks_grouping2[counter_grouping]/total_g2_areas
        
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

def get_function_first(element, mode):
    reference={'T':['i'], 'D':['v', 'vii'], 'SD': ['ii', 'iv', 'vi'], 'MED': ['iii']}

    # Spetial chords 
    if any([i for i in ('It','Ger', 'Fr') if i in element]):
        return 'D'

    elif element.lower()=='bii':
        return 'NAP'
    
    elif element.lower() in ['#vii', 'vii']:
        return 'D'

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

    if mode == 'm':
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


    element=element.replace('b','-') # '-' represents flats
    for key, value in reference.items():
        if element.replace('#','').replace('-','').lower() in value:
            output = key.lower() if element.islower() else key
            if '-' in element:
                output='-'+ output
            elif '#' in element:
                output='#' + output
            return output.replace('-','b')

def get_function_second(element):
    element=element.replace('b','-')
    if element.lower() == '#ln':
        return '#ST'
    elif element in ['rm', 'rj']:
        return 'rel'
    elif element.upper() in ['ST', 'LN']:
        return 'ST'
    else:
        return element.upper().replace('-','b')

def get_numerals(lausanne_table):
    numerals = lausanne_table.numeral.dropna().tolist()
    keys = lausanne_table.globalkey.dropna().tolist()
    relativeroots = lausanne_table.relativeroot.tolist()  

    _, ng2 = get_numerals_lists(numerals, relativeroots, keys) # por que se coge solo la funcion segunda?? anyway cojamos los numerals
    numerals_counter= Counter(numerals)
    # numerals_counter = Counter(ng2)
    
    total_numerals=sum(list(numerals_counter.values()))
    nc = {}
    for n in numerals_counter:
        if str(n)=='':
            raise Exception('Some chords here are not parsed well')
            continue
        nc['Numerals_'+str(n)] = round((numerals_counter[n]/total_numerals), 3)
    return nc 

def get_first_numeral(numeral, relativeroot, local_key):
    if str(relativeroot) != 'nan':
        return get_function_first(numeral, 'M' if relativeroot.isupper() else 'm')
    else:
        return get_function_first(numeral, 'M' if local_key.isupper() else 'm')

def get_numerals_lists(list_numerals, list_relativeroots, list_local_keys):
    tuples = list(zip(list_numerals, list_relativeroots, list_local_keys))
    result_dict = {t: get_first_numeral(*t) for t in set(tuples)}
    function1 = [result_dict[t] for t in tuples]
    function2 = [get_function_second(g1) for g1 in function1]
    return function1, function2

def get_additions(lausanne_table):
    additions = lausanne_table.changes.tolist()
    additions_cleaned = []
    for i, a in enumerate(additions):
        if isinstance(a, int):
            additions_cleaned.append(int(a))
        else:
            additions_cleaned.append(str(a))

    additions_counter = Counter(additions_cleaned)
    additions_dict = {ADDITIONS_4_6_64_74_94: 0, 
                        ADDITIONS_9: 0,
                        OTHERS_NO_AUG: 0, 
                        OTHERS_AUG: 0}
    for a in additions_counter:
        c = additions_counter[a]
        a = str(a)
        if a == '+9':
            additions_dict[ADDITIONS_9] = c
        elif a in ['4', '6', '64', '74', '94', '4.0', '6.0', '64.0', '74.0', '94.0']:
            additions_dict[ADDITIONS_4_6_64_74_94] += c
        elif '+' in a:
            additions_dict[OTHERS_AUG] += c
        elif str(a) =='nan':
            continue
        else:
            additions_dict[OTHERS_NO_AUG] += c

    additions = {}
    for a in additions_counter:
        if additions_counter[a] != 0:
            additions['Additions_'+str(a)] = additions_counter[a] / sum(list(additions_counter.values()))
    return additions
    
def get_chord_types(lausanne_table):

    chords_forms = make_type_col(lausanne_table) #Nan values represent {} notations, not chords
        
    grouped_forms = get_chord_types_groupings(chords_forms)

    form_counter = Counter(grouped_forms)
    features_chords= {}
    for f in form_counter:
        features_chords[CHORD_TYPES_prefix + str(f)] = form_counter[f] / sum(list(form_counter.values()))
    return features_chords

def get_chords(harmonic_analysis):
    
    relativeroots = harmonic_analysis.relativeroot.tolist()
    keys = harmonic_analysis.localkey.dropna().tolist() 
    chords = harmonic_analysis.chord.dropna().tolist()
    numerals=harmonic_analysis.numeral.dropna().tolist()
    types = harmonic_analysis.chord_type.dropna().tolist()
    chords_functionalities1, chords_functionalities2 = get_chords_functions(chords, relativeroots, keys)
    
    numerals_and_types =  [str(chord)+str(types[index]) if (str(types[index]) not in ('M','m')) else str(chord) for index, chord in enumerate(numerals)] 
    chords_dict = CountChords(numerals_and_types)
    
    # Exception for #viio chords
    if 'Chord_#viio' in chords_dict:
        chords_dict['Chord_viio']=chords_dict['Chord_viio'] + chords_dict.pop('Chord_#viio') if 'Chord_viio' in chords_dict else chords_dict.pop('Chord_#viio')

    counter_function_1 = Counter(chords_functionalities1)
    counter_function_2 = Counter(chords_functionalities2)
    chords_group_1 = CountChordsGroup(counter_function_1, '1')
    chords_group_2 = CountChordsGroup(counter_function_2, '2')

    return chords_dict, chords_group_1, chords_group_2

def CountChords(chords):
    chords_numbers = Counter(chords)
    total_chords=sum(chords_numbers.values())

    chords_dict = {}
    for degree in chords_numbers:
        chords_dict[CHORD_prefix+degree] = chords_numbers[degree]/total_chords
    return chords_dict

def CountChordsGroup(counter_function, number):
    chords_group = {}
    total_chords_group=sum(Counter(counter_function).values())

    for degree in counter_function:
        chords_group[CHORDS_GROUPING_prefix + number + degree] = counter_function[degree]/total_chords_group

    return chords_group

def parse_chord(chord):
    if '(' in chord:
        chord = chord.split('(')[0]
    if 'o' in chord:
        chord = chord.split('o')[0]
    if '+' in chord:
        chord = chord.split('+')[0]
    if '%' in chord:
        chord = chord.split('%')[0]
    if 'M' in chord:
        chord = chord.split('M')[0]
        
    # return chord letter without number
    return re.split('(\d+)', chord)[0]

def get_chord_type(chord_type):
    chord_type=str(chord_type)
    if chord_type=='m':
        return 'minor triad'
    elif chord_type=='M':
        return 'mayor triad'
    elif chord_type in ['7', 'mm7', 'Mm7', 'MM7', 'mM7']:
        return '7th'
    elif chord_type in ['o', 'o7', '%', '%7']:
        return 'dim'
    elif chord_type in ['+', '+M7', '+m7']:
        return 'aug'
    else:
        print("Chord type ", str(chord_type), 'not observed')
        return ''

def get_chord_types_groupings(chordtype_list):
    return [get_chord_type(chord_type) for chord_type in chordtype_list]


def get_first_chord_local(chord, local_key):
    #perseguir It6/V

    # local_key_mode = 'M' if local_key else 'm'
    local_key_mode = 'M' if local_key.isupper() else 'm'

    if '/' not in chord:
        return get_function_first(parse_chord(chord), local_key_mode)
    else: 
        parts = chord.split('/')
        degree = get_function_first(parse_chord(parts[0]), 'M' if parts[1].isupper() else 'm')
        if len(parts) == 2:
            # relative = get_function_first(parts[1], local_key_mode)
            # return '/'.join([degree, relative])
            return degree

        else:
            relative_list=[]
            relative_list.append(degree)
            relative_list.append(get_function_first(parts[1], 'M' if parts[2].isupper() else 'm'))
            for i in range(2,len(parts)):
                relative_list.append(get_function_first(parts[i], local_key_mode))
            # return '/'.join(relative_list)
            return degree

# REVIEW porqué es tan parecida a get_first_chord_local??
# Function to return second grouping for any chord in any given local key,
def get_second_grouping_localkey(first_grouping, relativeroot, local_key):
    mode = 'M' if local_key else 'm'
    #Qué es relative root aqui exactamente
    if str(relativeroot) != 'nan':
        mode = 'M' if relativeroot.isupper() else 'm'
    parts = first_grouping.split('/')
    
    degree = get_function_second(parts[0])
    if len(parts) == 2:
        chords = get_function_second(parts[1])#, mode)
        return degree
        # return '/'.join([degree, chords])
        
    elif len(parts) == 3:
        # chord_1 = get_degree_2(parts[1], )
        relative_1 = get_function_second(parts[1])#, 'M' if parts[2].isupper() else 'm')
        relative_2 = get_function_second(parts[2])#, mode)
        return '/'.join([degree, relative_1, relative_2])
    return degree

def get_chords_functions(chords, relativeroots, local_keys)-> list:

    #TODO: review that the order is not changed.

    chords_localkeys = list(zip(chords, local_keys))
    functionalities_dict = {t: get_first_chord_local(*t) for t in set(chords_localkeys)}

    function_first = [functionalities_dict[t] for t in chords_localkeys]

    #Redefine chords_localkeys to get second chord's functionality
    second_chords_localkeys = list(zip(function_first, relativeroots, local_keys))
    function_second = [get_second_grouping_localkey(*first_grouping) for first_grouping in second_chords_localkeys]

    return function_first, function_second

def make_type_col(df, num_col='numeral', form_col='form', fig_col='figbass'):
    param_tuples = list(df[[num_col, form_col, fig_col]].itertuples(index=False, name=None))
    result_dict = {t: features2type(*t) for t in set(param_tuples)}
    return pd.Series([result_dict[t] for t in param_tuples], index=df.index, name='chordtype').dropna()



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
    if not isinstance(labels, pd.Series):
        if isinstance(labels, pd.DataFrame):
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

    
# def split_labels(labels, git_branch='master', dropna=True):
#     """ Split DCML harmony labels into their respective features using the regEx
#         from the indicated branch of the DCMLab/standards repository.
#     Parameters
#     ----------
#     labels : :obj:`pandas.Series`
#         Harmony labels to be split.
#     git_branch : :obj:`str`, optional
#         The branch of the DCMLab/standards repo from which you want to use the regEx.
#     dropna : :obj:`bool`, optional
#         Drop rows where the regEx didn't match.
#     """
#     global REGEX
#     if git_branch not in REGEX:
#         url = f"https://raw.githubusercontent.com/DCMLab/standards/{git_branch}/harmony.py"
#         glo, loc = {}, {}
#         exec(urlopen(url).read(), glo, loc)
#         REGEX[git_branch] = re.compile(loc['regex'], re.VERBOSE)
#     regex = REGEX[git_branch]
#     cols = ['globalkey', 'localkey', 'pedal', 'chord', 'numeral', 'form', 'figbass', 'changes', 'relativeroot', 'pedalend', 'phraseend']
#     res = labels.str.extract(regex, expand=True)[cols]
#     if dropna:
#         return res.dropna(how='all').fillna('')
#     return res.fillna('')
