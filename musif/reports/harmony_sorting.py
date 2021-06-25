import copy
import os

#######################################################################################
# This function returns the most appropiate sortings for variables in harmonic analysis#
########################################################################################


def get_localkey_sorting():
    return 0
    # returns sorting of local keys 

def get_relativeroot_sorting():
    # returns sorting of scale degrees, by usual relative presence in tonal music, first major, then minor.
    return ['', 'I', 'i', 'V', 'vii', '#vii', 'IV', 'iv', 'II', 'ii', 'VI', 'vi', 'v', 'III', 'iii', 'bVII', 'VII', '#iv', 'bII', 'bii', 
            '#i', 'bIII', 'bVI', 'bvi', 'bI', 'bi', '#I', '#II', '#ii', 'biii', '#III', '#iii', 'bIV', 'biv', '#IV', 'bV', 'bv', '#V', 
            '#v', '#VI', '#vi', 'bvii', '#VII']

def get_modulations_sorting():
    # retuns sorting of modulations, with relative degrees before V and IV.
    return ['I', 'i', 'vi', 'III', 'V', 'IV', 'VI', 'II', 'iv', 'ii', 'v', 'VII', 'bII', 'bii', 'iii', 'vii', 'bI', 'bi', '#I', '#i', '#II', '#ii', 'bIII', 'biii', '#III', '#iii', 'bIV', 'biv', 
            '#IV', '#iv', 'bV', 'bv', '#V', '#v', 'bVI', 'bvi', '#VI', '#vi', 'bVII', 'bvii', '#VII', '#vii']

def get_modulationsGrouping1_sorting():
    # returns sorting of tonal functions, but usual frequency (descending).
    return ['T', 't', 'rm', 'rj', 'D', 'SD', 'sd', 'd', 'M', 'm', 'ST', 'st', 'NAP', 'nap', 'LN', 'ln', 'bST', 'bst', '#SD', '#sd', 'bSD', 'bsd', 'bT', 'bt', '#T', '#t', 'bD', 'bd', '#D', '#d', 'bM', 'bm', '#M', '#m', '#ST', '#st']

def get_modulationsGrouping2_sorting():
    # returns sorting of grouped tonal functions.
    return ['T', 'rel', 'D', 'SD', 'NAP', 'SM', 'ST', 'bST', '#SD', 'bSD', 'bT', '#T', 'bD', '#D', 'bSM', '#SM', '#ST']

def get_degrees_sorting():
    # returns sorting for chord degrees, tonic chords gaing first; then dominant and subdominant.
    return ['I', 'i', 'V', 'vii', '#vii', 'It', 'Ger', 'Fr', 'IV', 'iv', 'II', 'ii', 'VI', 'vi', 'v', 'III', 'iii', 'bVII', 'VII', '#iv', 'bII', 'bii', '#i', 'bIII', 'bVI', 'bvi', 'bI', 'bi', '#I', '#II', '#ii', 'biii', '#III', '#iii', 'bIV', 'biv', '#IV', 'bV', 'bv', '#V', '#v', '#VI', '#vi', 'bvii', '#VII']

def get_chordform_sorting():
    # returns sorting of chord forms.
    return ['', 'o', '%', 'M', '+']
    
def get_chordtype_sorting():
    # returns sorting of chord types.
    chordtypes = ['', 'M', 'm', 'Mm7', 'mm7', 'o', 'o7', '%7', 'MM7', 'mM7', '+', '+7', '+m7']
    groupings = ['triad', '7th', 'dim', 'aug']
    return chordtypes, groupings

def get_chordsGrouping1_sorting():
    # retuns sorting of 1st-level (tonal function) grouping for chords.
    combinations_level1 = []
    combinations_level2 = []
    numerals = ['T', 't', 'D', 'd', 'SD', 'sd', 'ST', 'NAP', 'st', 'M', 'm', 'bT', 'bt', '#T', '#t', 'bSD', 'bsd', '#SD', '#sd', 'bD', 'bd', '#D', '#d', 'bST', 'bst', '#ST', '#st', 'bM', 'bm', '#M', '#m', '#LN', '#ln']
    for n in numerals:
        n_c = [num + '/' + n for num in numerals]
        combinations_level1 += n_c
        n_c_2 = [nc + '/' + n for nc in n_c]
        combinations_level2 += n_c
    return numerals + combinations_level1 + combinations_level2

    
def get_chordsGrouping2_sorting():
    # retuns sorting of 2nd-level (tonal function, disregarding mode) grouping for chords.
    numerals = ['T', 'D', 'SD', 'M', 'ST', 'NAP', '#SD', 'bSD', '#T', 'bT', '#M', 'bM', '#D', 'bD', 'bST', '#ST']
    combinations_level1 = []
    combinations_level2 = []
    for n in numerals:
        n_c = [num + '/' + n for num in numerals]
        combinations_level1 += n_c
        n_c_2 = [nc + '/' + n for nc in n_c]
        combinations_level2 += n_c
    return numerals + combinations_level1 + combinations_level2

def get_inversions_sorting():
    # returns sorting for chord inversions (root, first, second, third)
    return ['', '6', '64', '7', '65', '43', '2']
    
    