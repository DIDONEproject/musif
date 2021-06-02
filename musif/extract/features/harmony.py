import glob

from ms3.score import MSCX
from musif.config import Configuration
import os
from collections import Counter, OrderedDict, defaultdict
from typing import List, Tuple

import ms3
import pandas as pd
from music21 import *
import itertools

from musif.extract.features.prefix import get_score_prefix
from pandas import DataFrame
from musif.extract.features.tempo import NUMBER_OF_BEATS

ALPHA = "abcdefghijklmnopqrstuvwxyz"

###############################################################################
# This function generates a dataframe with the measures and the local key     #
# present in each one of them based on the 'modulations' atribute in the json #
###############################################################################
def compute_modulations(partVoice, partVoice_expanded, modulations):
    try:
        measures = [m.measureNumber for m in partVoice]
        measures_expanded = [m.measureNumber for m in partVoice_expanded]
        
        first_modulation = modulations[0]
        key = []
        for m in modulations[1:]:
            key += [first_modulation[0]] * measures.index(m[1] - first_modulation[1] + 1)
            first_modulation = m
        key += [first_modulation[0]] * (measures[-1] - first_modulation[1] + 1)
        if measures[-1] != measures_expanded[-1]: #there are repetitions TODO: test
            measures_expanded = measures_expanded[measures_expanded.index(measures[-1]):] #change the starting point
            first_modulation = modulations[0]
            for m in modulations[1:]:
                if m[1] <= len(measures_expanded):
                    key += [first_modulation[0]] * measures_expanded.index(m[1] - first_modulation[1] + 1)
                    first_modulation = m
        return pd.DataFrame({'measures_continued': measures_expanded, 'key': key})
    except:
        print('Please, review the format of the modulation\'s indications in the JSON file. It needs to have the following format: [(<local key>, <starting measure>), ... ]')
        return None
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

def get_harmonic_rhythm(tabla_lausanne, sections):
    compases = tabla_lausanne.mc.dropna().tolist()
    beats = tabla_lausanne.mc_onset.dropna().tolist()
    voice = ['N' if str(v) == 'nan' else v for v in tabla_lausanne.voice.tolist()]
    time_signatures = tabla_lausanne.timesig.tolist()
    compases_voz = get_compases_per_possibility(list(set(voice)), compases, voice, beats, time_signatures)
    annotations_voz = {'Voice': voice.count(1), 'No_voice': voice.count(0)}
    compases_voz['Voice'] = compases_voz.pop(1) if 1 in compases_voz else 0
    compases_voz['No_voice'] = compases_voz.pop(0) if 0 in compases_voz else 0
    compases_section = get_compases_per_possibility(list(set(sections)), compases, sections, beats, time_signatures)
    annotations_sections = {k:sections.count(k) for k in compases_section}
    everything = dict(compases_voz, **compases_section)
    list_annotations = dict(annotations_voz, **annotations_sections)
    for k in everything:
        everything[k] = round(everything[k]/list_annotations[k] if list_annotations[k] != 0 else 0, 2)
    
    avg = sum(list(everything.values())) / (len(everything))
    
    return dict(everything, **{'Average': avg})

def get_chords(tabla_lausanne):
    chords = tabla_lausanne.chord.dropna().tolist()
    relativeroots = tabla_lausanne.relativeroot.tolist() 
    keys = tabla_lausanne.localkey.dropna().tolist() # TODO: comprobar en el 'enunciado' que en Chords hay que obtener la local key y no la global

    cg1, cg2 = harmony_groupings.get_chords_functions(chords, relativeroots, keys)
    c_c = Counter(chords)
    cg1 = Counter(cg1)
    cg2 = Counter(cg2)

    #chords
    c = {}
    for cc in c_c:
        c['Chords'+cc] = c_c[cc]

    #chords group 1
    c1 = {}
    for cc in cg1:
        c1['ChordsGroupping1'+ cc] = cg1[cc]
    
    #chords group 2
    c2 = {}
    for cc in cg2:
        c2['ChordsGroupping2' + cc] = cg2[cc]
    return c, c1, c2

def get_chord_types(tabla_lausanne):
    form = tabla_lausanne.form.tolist()
    #los que son nan hay que cambiarlos en función de una serie de reglas
    figbass = tabla_lausanne.figbass.tolist()
    numerals = tabla_lausanne.numeral.tolist()
    form_l = lausanne_sorting_script.make_type_col(tabla_lausanne)
        
    #convert the list of forms in their groups
    grouped_forms = harmony_groupings.get_chordtype_functions(form_l)

    form_counter = Counter(grouped_forms)
    fc = {}
    for f in form_counter:
        fc['Chord types' + str(f)] = str(round((form_counter[f] / sum(list(form_counter.values()))) * 100, 2)) + '%'
    return fc

def get_numerals(tabla_lausanne):
    numerals = tabla_lausanne.numeral.dropna().tolist()
    #numerals_defined = harmonic_analysis.Numerals_firstLetter.dropna().tolist()
    keys = tabla_lausanne.globalkey.dropna().tolist()
    relativeroots = tabla_lausanne.relativeroot.tolist()
    """
    list_grouppings = []
    for x, i in enumerate(numerals):
        #TODO cuando tengamos los chords de 3, ver cómo coger los grouppings
        if str(relativeroot[x]) != 'nan': # or '/' in chord
            major = relativeroot[x].isupper()
        else: 
            major = keys[x].isupper()
        grouping = harmonic_analysis['NFLG2M' if major else 'NFLG2m'].tolist()
        
        try:
            first_characters = parse_chord(i)
            grado = numerals_defined.index(first_characters)
            a = grouping[grado]    
            if str(a) == 'nan':
                print('nan numeral with ', i) #TODO: #vii sigue fallando, major no se coge bien. Repasar las condiciones
            list_general_groupings.append(a)
        except:
            print('Falta el numeral: ', i) """

    _, ng2 = harmony_groupings.get_numerals_function(numerals, relativeroots, keys)
    numerals_counter = Counter(ng2)
    
    nc = {}
    for n in numerals_counter:
        nc['Numerals'+str(n)] = str(round((numerals_counter[n]/sum(list(numerals_counter.values()))) * 100, 2)) + '%'
    return nc 

def get_modulations(tabla_lausanne, sections, major = True):
    keys = tabla_lausanne.localkey.dropna().tolist()
    grouping, _ = harmony_groupings.get_keys_functions(keys, mode = 'M' if major else 'm')
    modulations_sections = {g:[] for g in grouping}
    # Count the number of sections in each key
    last_key = ''
    for i, k in enumerate(keys):
        if (k != 'I' and k != 'i') and k != last_key: #premisa
            section = sections[i]
            last_key = k
            modulation = grouping[i]
            modulations_sections[modulation].append(section)
        if last_key == k and sections[i] != section:
            section = sections[i]
            modulations_sections[modulation].append(section)
    
    #borramos las modulaciones con listas vacías y dejamos un counter en vez de una lista
    ms = {}
    for m in modulations_sections:
        if len(modulations_sections[m]) != 0:
            ms['Modulations'+str(m)] = len(list(set(modulations_sections[m])))
    return ms

def get_additions(tabla_lausanne):
    additions = tabla_lausanne.changes.tolist()
    additions_cleaned = []
    for i, a in enumerate(additions):
        try:
            a_int = int(a)
            additions_cleaned.append(str(a_int))
        except:
            additions_cleaned.append(str(a))
    a_c = Counter(additions_cleaned)
   
    additions_counter = {'4, 6, 64, 74 & 94': 0, 
                        '+9': 0,
                        'Others without +': 0, 
                        'Others with +': 0}

    for a in a_c:
        c = a_c[a]
        a = str(a)
        
        if a == '+9':
            additions_counter[a] = c
        elif a in ['4', '6', '64', '74', '94', '4.0', '6.0', '64.0', '74.0', '94.0']:
            additions_counter['4, 6, 64, 74 & 94'] += c
        elif '+' in a:
            additions_counter['Others with +'] += c
        else:
            additions_counter['Others without +'] += c

    ad = {}
    for a in additions_counter:
        if additions_counter[a] != 0:
            ad['Additions'+str(a)] = str(round((additions_counter[a] / sum(list(additions_counter.values())))*100, 2)) + '%'
    return ad

def get_harmony_data(general_variables, harmonic_analysis, sections):
    hr = get_harmonic_rhythm(harmonic_analysis, sections)
    #le añadimos harmonic_rhythm delante de cada key
    harmonic_rhythm = {'Harmonic rhythm'+k: hr[k] for k in hr}
    # 2. Modulations TODO: revvisar
    modulations = get_modulations(harmonic_analysis, sections, major = general_variables['Mode'] == 'major')
    # 3. Numerals
    numerals = get_numerals(harmonic_analysis)
    # 4. Chord_types
    chord_types = get_chord_types(harmonic_analysis) 
    # 5. Additions
    additions = get_additions(harmonic_analysis)

    key_name = general_variables['Key'].split(" ")[0].strip().replace('-','b') #coger solo la string de antes del espacio? y así quitar major y minor
    key_name = key_name if general_variables['Mode'] == 'major' else key_name.lower()
    general_variables['Key'] = key_name

    return dict(general_variables, **harmonic_rhythm, **modulations, **numerals, **chord_types, **additions)


def parse_score(mscx_file: str):
    harmonic_analysis = None
    msc3_score = ms3.score.MSCX(mscx_file, level = 'c')
    has_table = True
    try:
        harmonic_analysis = msc3_score.expanded
    except Exception as e:
        has_table = False

    return harmonic_analysis, has_table

def get_score_features(score_data, parts_data, _cfg, parts_features, score_features) -> dict:
    path=score_data['mscx_path']
    _cfg.read_logger.info('')

    #erohnvoerbhotbobhsdvav

    #### GET FILE FROM LAUSSANE OR FROM MODULATIONS IN THE JSON_DATA ####
    # modulations = json_data['Modulations'] if 'Modulations' in json_data and len(json_data['Modulations']) != 0 else None
    
    
    #
    # gv = dict(name_variables, **excel_variables, **general_variables, **grouped_variables, **scoring_variables, **clef_dic, **total) 
    
    if 'mscx_path' in score_data:
            try:                
                # This takes a while!!
                harmonic_analysis, has_table = parse_score(path)

                has_table = True

            except:
                has_table = False

    # elif modulations is not None: # The user may have written only the not-expanded version
    #     has_table = True

    #     if modulations is not None and harmonic_analysis is None:
    #         harmonic_analysis = compute_modulations(partVoice, partVoice_expanded, modulations) #TODO: Ver qué pasa con par voice y como se puede hacer con la info que tenemos
    # #         pass
        
    #     score = score_data['score']
    repeat_elements= score_data['repetition_elements']
#     repeat_elements = get_repeat_elements(score, v = False)

    #     #!
        # score_expanded = expand_score_repetitions(score, repeat_elements)
    #     # Obtain score sections:
    #     sections = musical_form.get_form_measures(score, repeat_elements) #TODO: prove functionality
        
    #     Get the array based on harmonic_analysis.mc
    #     sections = continued_sections(sections, harmonic_analysis.mc)

        ################
        # HARMONY DATA #
        ################
        
        # TODO: Mirar que es exactamente lo que necesitamos para suplantar a la variable gv

        # final_dictionary_all_info = get_harmony_data(score_data, harmonic_analysis, sections)
        
        # #############
        # # KEY AREAS #
        # #############
        # keyareas = get_keyareas(harmonic_analysis, sections, major = general_variables['Mode'] == 'major')
        # final_dictionary_keyAreas = dict(gv, **keyareas)

        # #############
        # #  CHORDS   #
        # #############
        # chords, chords_g1, chords_g2 = get_chords(harmonic_analysis)
        # final_dictionary_chords = dict(gv, **chords, **chords_g1, **chords_g2)

        #     # df_score_harmony = msc3_score
        # else:
        # features = {} 
        #     return list(OrderedDict.fromkeys(sections))
        # features[f"{score_prefix}{NOTES}"] = notes
    #     score_prefix = get_score_prefix()
    # else:
    #     features = {} 

    # return features#, df_score_harmony

if __name__=='__main__':
    musescore_folder =r'../../../arias/mscx'
    xml_name = r'Dem01M-O_piu-1735-Leo[1.01][0430]'
    mscx_file = [f for f in list(glob.glob(os.path.join(musescore_folder, '*.mscx'))) if xml_name in f][0]
    msc3_score = ms3.score.MSCX(mscx_file, level = 'c')
    has_table = True
    try:
        harmonic_analysis = msc3_score.expanded
    except Exception as e:
        has_table = False
    xml_file=xml_name+'.xml'
    score = converter.parse(xml_file) #EN ESTE CASO NO NECESITAMOS EXPANDIR LAS REPETICIONES
    
    repeat_elements = get_repeat_elements(score, v = False)
    score_expanded = expand_score_repetitions(score, repeat_elements)
    # Obtain score sections:
    sections = musical_form.get_form_measures(score, repeat_elements) #TODO: prove functionality
    # Get the array based on harmonic_analysis.mc
    sections = continued_sections(sections, harmonic_analysis.mc)

    #data already processed in the extractor
    gv = dict(name_variables, **excel_variables, **general_variables, **grouped_variables, **scoring_variables, **clef_dic, **total) 

    ################
    # HARMONY DATA #
    ################
    final_dictionary_all_info = get_harmony_data(gv, harmonic_analysis, sections)

    #############
    # KEY AREAS #
    #############
    keyareas = get_keyareas(harmonic_analysis, sections, major = general_variables['Mode'] == 'major')
    final_dictionary_keyAreas = dict(gv, **keyareas)

    #############
    #  CHORDS   #
    #############
    chords, chords_g1, chords_g2 = get_chords(harmonic_analysis)
    final_dictionary_chords = dict(gv, **chords, **chords_g1, **chords_g2)
    

