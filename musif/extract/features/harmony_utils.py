from collections import Counter
import pandas as pd
####################
# METRICAL ANALYSIS
####################    

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
#########################################################################
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
################################################################################
def get_localkey_function1(localkey, mode):
    if mode == 'M':
        if localkey in ['I']:
            return 'T'
        elif localkey in ['i']:
            return 't'
        elif localkey in ['vi']:
            return 'rm'
        elif localkey in ['V', 'vii']:
            return 'D'
        elif localkey in ['v']:
            return 'd'
        elif localkey in ['II', 'IV', 'VI']:
            return 'SD'
        elif localkey in ['ii', 'iv']:
            return 'sd'
        elif localkey in ['bII']:
            return 'NAP'
        elif localkey in ['bVII']:
            return 'ST'
        elif localkey in ['III']:
            return 'M'
        elif localkey in ['iii']:
            return 'm'
        elif localkey in ['bI']:
            return 'bT'
        elif localkey in ['bi']:
            return 'bt'
        elif localkey in ['#I']:
            return '#T'
        elif localkey in ['#i']:
            return '#t'
        elif localkey in ['#V']:
            return '#D'
        elif localkey in ['#v']:
            return '#d'
        elif localkey in ['bIV', 'bVI']:
            return 'bSD'
        elif localkey in ['bii', 'biv', 'bvi']:
            return 'bsd'
        elif localkey in ['#II', '#IV', '#vi']:
            return '#SD'
        elif localkey in ['#ii', '#iv', '#vi']:
            return '#sd'
        elif localkey in ['bIII']:
            return 'bM'
        elif localkey in ['biii']:
            return 'bm'
        elif localkey in ['#III']:
            return '#M'
        elif localkey in ['#iii']:
            return '#m'
        elif localkey in ['bvii']:
            return 'st'
        elif localkey in ['VII']:
            return 'LN'
        elif localkey in ['#VII']:
            return '#LN'
        elif localkey in ['#vii']:
            return '#ln'
        else:
            print('Error in get_localkey_function1 with localkey', localkey)
    else: #minor mode
        if localkey in ['I']:
            return 'T'
        elif localkey in ['i']:
            return 't'
        elif localkey in ['III']:
            return 'rj'
        elif localkey in ['V', '#vii']:
            return 'D'
        elif localkey in ['v']:
            return 'd'
        elif localkey in ['II', 'IV', 'VI']:
            return 'SD'
        elif localkey in ['ii', 'iv', 'vi']:
            return 'sd'
        elif localkey in ['bII']:
            return 'NAP'
        elif localkey in ['iii']:
            return 'm'
        elif localkey in ['VII']:
            return 'ST'
        elif localkey in ['bI']:
            return 'bT'
        elif localkey in ['bi']:
            return 'bt'
        elif localkey in ['#I']:
            return '#T'
        elif localkey in ['#i']:
            return '#t'
        elif localkey in ['#V']:
            return '#D'
        elif localkey in ['#v']:
            return '#d'
        elif localkey in ['bIV', 'bVI']:
            return 'bSD'
        elif localkey in ['bii', 'biv', 'bvi']:
            return 'bsd'
        elif localkey in ['#II', '#IV', '#vi']:
            return '#SD'
        elif localkey in ['#ii', '#iv', '#vi']:
            return '#sd'
        elif localkey in ['bIII']:
            return 'bM'
        elif localkey in ['biii']:
            return 'bm'
        elif localkey in ['#III']:
            return '#M'
        elif localkey in ['#iii']:
            return '#m'
        elif localkey in ['bVII']:
            return 'bST'
        elif localkey in ['bvii']:
            return 'bst'
        elif localkey in ['#VII']:
            return '#LN'
        elif localkey in ['vii']:
            return 'st'
        else:
            print('Error in get_localkey_function1 with localkey', localkey)

#############################################################
# Function to return function2 based on function1. It
# disregards the mode. #
#############################################################
def get_localkey_function2(chord):
    if chord in ['T', 't']:
        return 'T'
    elif chord in ['rm', 'rj']:
        return 'rel'
    elif chord in ['D', 'd']:
        return 'D'
    elif chord in ['SD', 'sd']:
        return 'SD'
    elif chord in ['NAP']:
        return 'NAP'
    elif chord in ['M', 'm']:
        return 'M'
    elif chord in ['ST', 'st', 'LN']:
        return 'ST'
    elif chord in ['bT', 'bt']:
        return 'bT'
    elif chord in ['#T', '#t']:
        return '#T'
    elif chord in ['bSD', 'bsd']:
        return 'bSD'
    elif chord in ['#SD', '#sd']:
        return '#SD'
    elif chord in ['bD', 'bd']:
        return 'bD'
    elif chord in ['#D', '#d']:
        return '#D'
    elif chord in ['bM', 'bm']:
        return 'bM'
    elif chord in ['#M', '#m']:
        return '#M'
    elif chord in ['bST', 'bst']:
        return 'bST'
    else:
        print('Error in get_key_function2 with', chord)

##############################################################
# Function to return harmonic functions (1 and 2) based on a list of keys #
##############################################################


def get_keys_functions(list_keys, mode):
    result_dict = {t: get_localkey_function1(t, mode) for t in set(list_keys)}
    function1 = [result_dict[t] for t in list_keys]
    function2 = [get_localkey_function2(g1) for g1 in function1]
    return function1, function2

def get_compases_per_possibility(possibilities, measures, possibilities_list, beats, time_signatures):
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
                num_compasses, done = compute_number_of_compasses(done, starting_measure, measures[i - 1], measures[i], beats[i - 1], n_beats)
                voice_measures[last_voice] += num_compasses
            last_voice = v
            starting_measure = measures[i] - 1
    
    #último!
    num_compasses, _ = compute_number_of_compasses(done, starting_measure, measures[numberofmeasures - 1], measures[numberofmeasures - 1] + 1, beats[numberofmeasures - 1], n_beats)
    voice_measures[last_voice] += num_compasses

    #comprobar que tiene sentido:
    # if (compases[0] != 0 and round(sum(list(compases_voz.values()))) != compases[i]) or (compases[0] == 0 and round(sum(list(compases_voz.values()))) != compases[i] + 1):
    #    print('Error en el recuento de compases de cada sección/voz en get_compases_per_possibility')

    return voice_measures

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

def get_keyareas(tabla_lausanne, sections, major = True):
    # indexes_A = [i for i, s in enumerate(sections) if s == "A"]
    # indexes_B = [i for i, s in enumerate(sections) if s == "B"]

    """possible_keys = harmonic_analysis.Chords.dropna().tolist()
    grouping1 = harmonic_analysis['GC1M' if major else 'GC1m'].dropna().tolist()
    grouping2 = harmonic_analysis['GC2M' if major else 'GC2m'].dropna().tolist()
    
    g1 = [grouping1[possible_keys.index(c)] for c in keys]
    g2 = [grouping2[possible_keys.index(c)] for c in keys]"""

    keys = tabla_lausanne.localkey.dropna().tolist()
    g1, g2 = get_keys_functions(keys, 'M' if major else 'm')

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
    measures = tabla_lausanne.mc.dropna().tolist()
    beats = tabla_lausanne.mc_onset.dropna().tolist()
    time_signatures = tabla_lausanne.timesig.tolist()
    """xml_ts = harmonic_analysis['TimeSignature'].dropna().tolist()
    xml_beats = harmonic_analysis['NoBeats'].dropna().tolist()
    relationship_timesignature_beats = {ts: xml_beats[i] for i, ts in enumerate(xml_ts)}"""
    key_compasses = get_compases_per_possibility(list(set(keys)), measures, keys, beats, time_signatures)
    total_compasses = sum(list(key_compasses.values()))
    key_compasses = {kc:key_compasses[kc]/total_compasses for kc in key_compasses}
    keyGroupping1_compasses = get_compases_per_possibility(list(set(g1)), measures, g1, beats, time_signatures)
    keyGroupping1_compasses = {kc:keyGroupping1_compasses[kc]/sum(list(keyGroupping1_compasses.values())) for kc in keyGroupping1_compasses}
    keyGroupping2_compasses = get_compases_per_possibility(list(set(g2)), measures, g2, beats, time_signatures)
    keyGroupping2_compasses = {kc:keyGroupping2_compasses[kc]/sum(list(keyGroupping2_compasses.values())) for kc in keyGroupping2_compasses}
    # SECTION A
    # measures_A = [measures[i] for i in indexes_A]
    # beats_A = [beats[i] for i in indexes_A]
    # time_signatures_A = [time_signatures[i] for i in indexes_A]
    # key_compasses_A = get_compases_per_possibility(list(set(A_Keys)), measures_A, A_Keys, beats_A, time_signatures_A)
    # total_compasses_A = sum(list(key_compasses_A.values()))
    # key_compasses_A = {kc:key_compasses_A[kc]/total_compasses_A for kc in key_compasses_A}
    # keyGroupping1_compasses_A = get_compases_per_possibility(list(set(g1_A)), measures_A, g1_A, beats_A, time_signatures_A)
    # keyGroupping1_compasses_A = {kc:keyGroupping1_compasses_A[kc]/sum(list(keyGroupping1_compasses_A.values())) for kc in keyGroupping1_compasses_A}
    # keyGroupping2_compasses_A = get_compases_per_possibility(list(set(g2_A)), measures_A, g2_A, beats_A, time_signatures_A)
    # keyGroupping2_compasses_A = {kc:keyGroupping2_compasses_A[kc]/sum(list(keyGroupping2_compasses_A.values())) for kc in keyGroupping2_compasses_A}
    # # SECTION B
    # measures_B = [measures[i] for i in indexes_B]
    # beats_B = [beats[i] for i in indexes_B]
    # time_signatures_B = [time_signatures[i] for i in indexes_B]
    # key_compasses_B = get_compases_per_possibility(list(set(B_Keys)), measures_B, B_Keys, beats_B, time_signatures_B)
    # total_compasses_B = sum(list(key_compasses_B.values()))
    # key_compasses_B = {kc:key_compasses_B[kc]/total_compasses_B for kc in key_compasses_B}
    # keyGroupping1_compasses_B = get_compases_per_possibility(list(set(g1_B)), measures_B, g1_B, beats_B, time_signatures_B)
    # keyGroupping1_compasses_B = {kc:keyGroupping1_compasses_B[kc]/sum(list(keyGroupping1_compasses_B.values())) for kc in keyGroupping1_compasses_B}
    # keyGroupping2_compasses_B = get_compases_per_possibility(list(set(g2_B)), measures_B, g2_B, beats_B, time_signatures_B)
    # keyGroupping2_compasses_B = {kc:keyGroupping2_compasses_B[kc]/sum(list(keyGroupping2_compasses_B.values())) for kc in keyGroupping2_compasses_B}

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
        keyareas['KeyGroupping1'+cg] = counter_grouping1[cg]
        keyareas['KeyGroupping1Compasses'+cg] = keyGroupping1_compasses[cg]
        keyareas['KeyGroupping1Modulatory'+cg] = counter_grouping1[cg]/total_g1_areas
        keyareas['KeyGroupping1ModComp'+cg] = (keyareas['KeyGroupping1Compasses'+cg] + keyareas['KeyGroupping1Modulatory'+cg]) / 2
    for cg in counter_grouping2:
        keyareas['KeyGroupping2'+cg] = counter_grouping2[cg]
        keyareas['KeyGroupping2Compasses'+cg] = keyGroupping2_compasses[cg]
        keyareas['KeyGroupping2Modulatory'+cg] = counter_grouping2[cg]/total_g2_areas
        keyareas['KeyGroupping2ModComp'+cg] = (keyareas['KeyGroupping2Compasses'+cg] + keyareas['KeyGroupping2Modulatory'+cg]) / 2

    # for ck in counter_keys_A:
    #     keyareas['KeySectionA'+ck] = counter_keys_A[ck]
    #     keyareas['KeyModCompSectionA'+ck] = (key_compasses_A[ck] + (counter_keys_A[ck]/total_key_areas_A)) / 2
    # for cg in counter_grouping1_A:
    #     keyareas['KeyGroupping1SectionA'+cg] = counter_grouping1_A[cg]
    #     keyareas['KeyGroupping1ModCompSectionA'+cg] = (keyGroupping1_compasses_A[cg] + (counter_grouping1_A[cg]/total_g1_areas_A)) / 2
    # for cg in counter_grouping2_A:
    #     keyareas['KeyGroupping2SectionA'+cg] = counter_grouping2_A[cg]
    #     keyareas['KeyGroupping2ModCompSectionA'+cg] = (keyGroupping2_compasses_A[cg] + (counter_grouping2_A[cg]/total_g2_areas_A)) / 2
    
    # for ck in counter_keys_B:
    #     keyareas['KeySectionB'+ck] = counter_keys_B[ck]
    #     keyareas['KeyModCompSectionB'+ck] = (key_compasses_B[ck] + (counter_keys_B[ck]/total_key_areas_B)) / 2
    # for cg in counter_grouping1_B:
    #     keyareas['KeyGroupping1SectionB'+cg] = counter_grouping1_B[cg]
    #     keyareas['KeyGroupping1ModCompSectionB'+cg] = (keyGroupping1_compasses_B[cg] + (counter_grouping1_B[cg]/total_g1_areas_B)) / 2
    # for cg in counter_grouping2_B:
    #     keyareas['KeyGroupping2SectionB'+cg] = counter_grouping2_B[cg]
    #     keyareas['KeyGroupping2ModCompSectionB'+cg] = (keyGroupping2_compasses_B[cg] + (counter_grouping2_B[cg]/total_g2_areas_B)) / 2

    return keyareas
# ####################
# DEGREES (for relative roots, numerals and chords)
####################

###########################################################################
# Function to obtain the harmonic function1 of every relativeroot, chord, or numeral#
# harmonic_analysis: columnas AG-AK
###########################################################################
def get_degree_function1(element, mode):
    # elements common to major and minor modes
    if element in ['I']:
        return 'T'
    elif element in ['i']:
        return 't'
    elif element in ['v']:
        return 'd'
    elif element in ['II', 'IV', 'VI']:
        return 'SD'
    elif element in ['ii', 'iv', 'vi']:
        return 'sd'
    elif element in ['bII']:
        return 'NAP'
    elif element in ['III']:
        return 'S'
    elif element in ['iii']:
        return 's'
    elif element in ['bI']:
        return 'bT'
    elif element in ['bi']:
        return 'bt'
    elif element in ['#I']:
        return '#T'
    elif element in ['#i']:
        return '#t'
    elif element in ['#V']:
        return '#D'
    elif element in ['#v']:
        return '#d'
    elif element in ['bIV', 'bVI']:
        return 'bSD'
    elif element in ['bii', 'biv', 'bvi']:
        return 'bsd'
    elif element in ['#II', '#IV']:
        return '#SD'
    elif element in ['#ii', '#iv', '#vi']:
        return '#sd'
    elif element in ['bIII']:
        return 'bM'
    elif element in ['biii']:
        return 'bm'
    elif element in ['#III']:
        return '#M'
    elif element in ['#iii']:
        return '#m'
    elif element in ['It', 'Ger', 'Fr']:
        return 'D'

    if mode == 'M':
        # elements specific of the major mode
        if element in ['V', 'vii']:
            return 'D'
        elif element in ['bVII']:
            return 'ST'
        elif element in ['bvii']:
            return 'st'
        elif element in ['VII']:
            return '#ST'
        elif element in ['#vii']:
            return '#ln'
        else:
            print(element, 'not available')
    else:
        # elements specific of the minor mode
        if element in ['V', '#vii']:
            return 'D'
        elif element in ['VII']:
            return 'ST'
        elif element in ['bVII']:
            return 'bST'
        elif element in ['bvii']:
            return 'bst'
        elif element in ['#VII']:
            return 'LN'
        elif element in ['vii']:
            return 'st'
        else:
            print(element, 'not available')
    return ''
###########################################################################
# Function to obtain the harmonic function2 of every relativeroot, chord, or numeral.
###########################################################################
def get_degree_function2(element):
    # if element.lower() == 't':
    #     return 'T'
    # elif element in ['D', 'd']:
    #     return 'D'
    # elif element in ['SD', 'sd']:
    #     return 'SD'
    # elif element in ['NAP']:
    #     return 'NAP'
    # elif element in ['M', 'm']:
    #     return 'M'
    # elif element in ['ST', 'st', 'LN', 'ln']:
    #     return 'ST'
    # elif element in ['bT', 'bt']:
    #     return 'bT'
    # elif element in ['#T', '#t']:
    #     return '#T'
    # elif element in ['bSD', 'bsd']:
    #     return 'bSD'
    # elif element in ['#SD', '#sd']:
    #     return '#SD'
    # elif element in ['bD', 'bd']:
    #     return 'bD'
    # elif element in ['#D', '#d']:
    #     return '#D'
    # elif element in ['bM', 'sm']:
    #     return 'SM'
    # elif element in ['#M', '#m']:
    #     return '#M'
    # elif element in ['bST', 'bst']:
    #     return 'bST'
    # elif element in ['#ST', '#ST','#LN', '#ln']:
    #     return '#ST'
    # else:
    #     print("Error, grouping1 ", element, " is not considered")
    # return ''
    return element.upper().replace('B','b')

####################
# NUMERALS
####################
def get_numeral_function1(numeral, relativeroot, local_key):
    if str(relativeroot) != 'nan':
        return get_degree_function1(numeral, 'M' if relativeroot.isupper() else 'm')
    else:
        return get_degree_function1(numeral, 'M' if local_key.isupper() else 'm')

def get_numeral_function2(grouping1):
    return get_degree_function2(grouping1)

def get_numerals_function(list_numerals, list_relativeroots, list_local_keys):
    tuples = list(zip(list_numerals, list_relativeroots, list_local_keys))
    result_dict = {t: get_numeral_function1(*t) for t in set(tuples)}
    function1 = [result_dict[t] for t in tuples]
    function2 = [get_numeral_function2(g1) for g1 in function1]
    return function1, function2
####################
# CHORDS
####################

#################################################################
# This function takes the first characters in the chord to 
# obtain its grouping
#################################################################
def parse_chord(chord):
    first_char = chord
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
    for c in first_char:
        try:
            c_int = int(c)
            break
        except:
            chars.append(c)

    return ''.join(chars)

####################
# CHORD FORM
####################

#############################################
# Function that returns the chord_type grouping
#############################################
def get_chordtype_function(chord_type):
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
        print("chordtype ", str(chord_type), 'not observed')
        return ''

#############################################
# Function that returns the chord_type grouping
#############################################
def get_chordtype_functions(chordtype_list):
    return [get_chordtype_function(chord_type) for chord_type in chordtype_list]


##################################################################
# Function to return the first grouping for any chord
# in any given local key.
##################################################################
def get_chord_function1(chord, local_key):
    mode = 'M' if local_key else 'm'
    if '/' not in chord:
        return get_degree_function1(parse_chord(chord), mode)
    else: # the chord has '/' 
        parts = chord.split('/')
        grado = get_degree_function1(parse_chord(parts[0]), 'M' if parts[1].isupper() else 'm')
        if len(parts) == 2:
            acorde = get_degree_function1(parts[1], mode)
            return '/'.join([grado, acorde])
        elif len(parts) == 3:
            acorde1 = get_degree_function1(parts[1], 'M' if parts[2].isupper() else 'm')
            acorde2 = get_degree_function1(parts[2], mode)
            return '/'.join([grado, acorde1, acorde2])

##################################################################
# Function to return the second grouping for any chord in any given local key,
##################################################################
def get_chord_function2(grouping1, relativeroot, local_key):
    mode = 'M' if local_key else 'm'
    if str(relativeroot) != 'nan':
        mode = 'M' if relativeroot.isupper() else 'm'
    parts = grouping1.split('/')
    grado = get_degree_function2(parts[0])
    if len(parts) == 2:
        acorde = get_degree_function2(parts[1])
        return '/'.join([grado, acorde])
    elif len(parts) == 3:
        acorde1 = get_degree_function2(parts[1], 'M' if parts[2].isupper() else 'm')
        acorde2 = get_degree_function2(parts[2])
        return '/'.join([grado, acorde1, acorde2])
    return grado

def get_chords_functions(list_chords, list_relativeroots, list_local_keys):
    #TODO: review that the order is not changed
    tuples = list(zip(list_chords, list_local_keys))
    result_dict = {t: get_chord_function1(*t) for t in set(tuples)}
    function1 = [result_dict[t] for t in tuples]
    tuples = list(zip(function1, list_relativeroots, list_local_keys))
    function2 = [get_chord_function2(*g1) for g1 in tuples]
    return function1, function2

def features2type(numeral, form=None, figbass=None):
    """ Turns a combination of the three chord features into a chord type.

    Returns
    -------
    'M':    Major triad
    'm':    Minor triad
    'o':    Diminished triad
    '+':    Augmented triad
    'mm7':  Minor seventh chord
    'Mm7':  Dominant seventh chord
    'MM7':  Major seventh chord
    'mM7':  Minor major seventh chord
    'o7':   Diminished seventh chord
    '%7':   Half-diminished seventh chord
    '+7':   Augmented (minor) seventh chord
    '+M7':  Augmented major seventh chord
    """
    if pd.isnull(numeral):
        return numeral
    form, figbass = tuple('' if pd.isnull(val) else val for val in (form, figbass))
    if type(figbass) is float:
        figbass = str(int(figbass))
    #triads
    if figbass in ['', '6', '64']:
        if form in ['o', '+']:
            return form
        if form in ['%', 'M']:
            if figbass == '':
                return f"{form}7"
            print(f"{form} is a seventh chord and cannot have figbass '{figbass}'")
            return None
        return 'm' if numeral.islower() else 'M'
    # seventh chords
    if form in ['o', '%', '+', '+M']:
        return f"{form}7"
    triad = 'm' if numeral.islower() else 'M'
    seventh = 'M' if form == 'M' else 'm'
    return f"{triad}{seventh}7"

def make_type_col(df, num_col='numeral', form_col='form', fig_col='figbass'):
    """ Create a new Series with the chord type for every row of `df`.
        Uses: features2type()
    """
    param_tuples = list(df[[num_col, form_col, fig_col]].itertuples(index=False, name=None))
    result_dict = {t: features2type(*t) for t in set(param_tuples)}
    return pd.Series([result_dict[t] for t in param_tuples], index=df.index, name='chordtype')
