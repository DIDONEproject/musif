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
def get_localkey_function2(function1):
    if function1 in ['T', 't']:
        return 'T'
    elif function1 in ['rm', 'rj']:
        return 'rel'
    elif function1 in ['D', 'd']:
        return 'D'
    elif function1 in ['SD', 'sd']:
        return 'SD'
    elif function1 in ['NAP']:
        return 'NAP'
    elif function1 in ['M', 'm']:
        return 'M'
    elif function1 in ['ST', 'st', 'LN']:
        return 'ST'
    elif function1 in ['bT', 'bt']:
        return 'bT'
    elif function1 in ['#T', '#t']:
        return '#T'
    elif function1 in ['bSD', 'bsd']:
        return 'bSD'
    elif function1 in ['#SD', '#sd']:
        return '#SD'
    elif function1 in ['bD', 'bd']:
        return 'bD'
    elif function1 in ['#D', '#d']:
        return '#D'
    elif function1 in ['bM', 'bm']:
        return 'bM'
    elif function1 in ['#M', '#m']:
        return '#M'
    elif function1 in ['bST', 'bst']:
        return 'bST'
    else:
        print('Error in get_key_function2 with', function1)

##############################################################
# Function to return harmonic functions (1 and 2) based on a list of keys #
##############################################################
def get_keys_functions(list_keys, mode):
    result_dict = {t: get_localkey_function1(t, mode) for t in set(list_keys)}
    function1 = [result_dict[t] for t in list_keys]
    function2 = [get_localkey_function2(g1) for g1 in function1]
    return function1, function2

####################
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
    if element in ['T', 't']:
        return 'T'
    elif element in ['D', 'd']:
        return 'D'
    elif element in ['SD', 'sd']:
        return 'SD'
    elif element in ['NAP']:
        return 'NAP'
    elif element in ['M', 'm']:
        return 'M'
    elif element in ['ST', 'st', 'LN', 'ln']:
        return 'ST'
    elif element in ['bT', 'bt']:
        return 'bT'
    elif element in ['#T', '#t']:
        return '#T'
    elif element in ['bSD', 'bsd']:
        return 'bSD'
    elif element in ['#SD', '#sd']:
        return '#SD'
    elif element in ['bD', 'bd']:
        return 'bD'
    elif element in ['#D', '#d']:
        return '#D'
    elif element in ['bM', 'sm']:
        return 'SM'
    elif element in ['#M', '#m']:
        return '#M'
    elif element in ['bST', 'bst']:
        return 'bST'
    elif element in ['#ST', '#ST','#LN', '#ln']:
        return '#ST'
    else:
        print("Error, grouping1 ", element, " is not considered")
    return ''

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