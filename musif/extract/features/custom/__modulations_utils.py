# ### MODULATIONS ###
from collections import Counter
from typing import List
from pandas.core.frame import DataFrame
import roman
import itertools
from music21 import scale, pitch
from music21.note import Note
# from .__harmony_utils import get_function_first, get_function_second
from musif.extract.features.custom.__harmony_utils import get_function_first, get_function_second

# REVIEW

def get_modulations(lausanne_table: DataFrame, sections, major = True):
    keys = lausanne_table.localkey.dropna().tolist()
    grouping, _ = get_keys_functions(keys, mode = 'M' if major else 'm')
    modulations_sections = {group:[] for group in grouping}
###
# Es el nº de secciones que están en cada tonalidad, 
# viendo las anotaciones como bloques. Nº enteros
    
    
    # TASK: Count the number of sections in each key ###
    ##sections has the same length that harnmonbic_abalysis dataframe
    last_key = ''
    for i, key in enumerate(keys):
        if (key.lower() != 'i') and key != last_key: #premisa
            section = sections[i] # busca la seccion que corresponde a ese compás
            last_key = key
            modulation = grouping[i] #busca la tonalidad que corresponde a este compas
            
            #esta variable es un dictionario con {'T': [], 'D': [], 'sd': []} donde se apendican en cada lista las secciones Cuantas secciones hay en cada tonalidad?
            modulations_sections[modulation].append(section)
        if last_key == key and sections[i] != section:
            section = sections[i]
            modulations_sections[modulation].append(section)
    
    #borramos las modulaciones con listas vacías y dejamos un counter en vez de una lista
    ms = {}
    for m in modulations_sections:
        if len(modulations_sections[m]) != 0:
            ms['Modulations'+str(m)] = len(list(set(modulations_sections[m])))
    return ms

def get_keys_functions(list_keys, mode):
    result_dict = {t: get_function_first(t, mode) for t in set(list_keys)}
    first_function = [result_dict[t] for t in list_keys]
    second_function = [get_function_second(g1) for g1 in first_function]
    return first_function, second_function
    
#########################################################################
# Como sections tiene una indicación por compás, pero a lo largo del script
# trabajamos con la tabla harmonic_analysis, que tiene tantas entradas por 
# compás como anotaciones harmónicas, repetimos las secciones según el número
#########################################################################
def continued_sections(sections: list, mc):
    extended_sections = []
    repeated_measures = Counter(mc)
    for i, c in enumerate(repeated_measures):
        extended_sections.append([sections[i]] * repeated_measures[c])
    # Flat list
    return list(itertools.chain(*extended_sections))
    
def IsAnacrusis(harmonic_analysis):
    return harmonic_analysis.mn.dropna().tolist()[0] == 0
    
def get_tonality_for_measure(harmonic_analysis, tonality, renumbered_measures):
    tonality_map = {}
    for index, grado in enumerate(harmonic_analysis.localkey):
        tonality_map[renumbered_measures[index]] = get_localTonalty(tonality, grado.strip())
    return tonality_map


def get_localTonalty(globalkey, degree):
    accidental=''
    if '#' in degree:
        accidental = '#'
        degree = degree.replace('#', '')

    elif 'b' in degree:
        accidental = '-'
        degree = degree.replace('b', '')

    degree_int = roman.fromRoman(degree.upper())

    if globalkey.replace('b', '').isupper():
        pitch_scale = scale.MajorScale(globalkey.split()[0]).pitchFromDegree(degree_int).name 
    else:
        pitch_scale = scale.MinorScale(globalkey.split(' ')[0]).pitchFromDegree(degree_int).name 
    
    modulation = pitch_scale + accidental

    # modulation = modulation.replace('#', '', 1)
    # modulation = modulation.replace('-', '', 1)

    return modulation.upper() if degree.isupper() else modulation.lower()
###########################################################################
# Function created to obtain the scale degree of a note in a given key #
###########################################################################
def get_note_degree(key, note):
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


##########################################################################################
# Transforms the list of notes into their scale degrees, based on the local key          #
##########################################################################################

def get_emphasised_scale_degrees_relative(notes_list: list, score_data: dict) -> List[list]:
    harmonic_analysis=score_data['MS3_score']
    tonality=score_data['tonality']
    notes_measures = []
    renumbered_measures = harmonic_analysis.mc.dropna().tolist()

    for note in notes_list:
      if note.isChord:
        note=note[0] #If we wave 2or more notes at once, we just take the lowest one

      notes_measures.append((note.name, note.measureNumber))


    if IsAnacrusis(harmonic_analysis): #Anacrussis:
        renumbered_measures = [rm - 1 for rm in renumbered_measures]
    
    tonality_map = get_tonality_for_measure(harmonic_analysis, tonality, renumbered_measures)

    Add_Missing_Measures_to_tonality_map(tonality_map,renumbered_measures)

    return get_emph_degrees(notes_list, tonality_map)

    
def Add_Missing_Measures_to_tonality_map(tonality_map: dict, renumbered_measures: list):
    for num in range(1, renumbered_measures[-1] + 1):
        if num not in tonality_map:
            tonality_map[num] = tonality_map[num - 1]
            
def get_emph_degrees(notes_list: List[Note], tonality_map: dict)-> dict:
    notes_per_degree_relative = {}
    error_compasses = []
    for note in notes_list:
        if note.isChord:
          note = note[0]

        note_name = note.name
        note_measure = note.measureNumber
        if note_measure in tonality_map:
            local_tonality = tonality_map[note_measure]
            degree_value = get_note_degree(local_tonality, note_name)

            if str(degree_value) not in notes_per_degree_relative:
                notes_per_degree_relative[str(degree_value)] = 1
            else:
                notes_per_degree_relative[str(degree_value)] += 1
        else:
            if note_measure not in error_compasses:
                error_compasses.append(note_measure)
    return notes_per_degree_relative, error_compasses