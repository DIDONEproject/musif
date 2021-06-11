import glob

from ms3.score import MSCX
from musif.config import Configuration
import os
from collections import Counter, OrderedDict, defaultdict
from typing import Dict, List, Tuple

import ms3
import pandas as pd
from music21 import *
import itertools

from musif.extract.features.prefix import get_score_prefix
from pandas import DataFrame
from musif.extract.features.tempo import NUMBER_OF_BEATS

from .harmony_utils import get_beatspertsig, compute_number_of_compasses, continued_sections, get_keys_functions, get_numerals_function, make_type_col, get_chords_functions, get_chordtype_functions, get_compases_per_possibility, get_keyareas
ALPHA = "abcdefghijklmnopqrstuvwxyz"


HARMONIC_RHYTHM_VOICE = "Harmonic rhythm Voice"
HARMONIC_RHYTHM_NOVOICE = "Harmonic rhythm No Voice"
HARMONIC_RHYTHM_AVERAGE = "Harmonic rhythm Average"
NUMERALS_T='Numerals_T'
NUMERALS_D='Numerals_D'
NUMERALS_SD='Numerals_SD'
NUMERALS_sharp_LN='Numerals_#LN'
NUMERALS='Numerals'

logger = None
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


def get_harmonic_rhythm(ms3_table, sections)-> dict:
    
    measures = ms3_table.mc.dropna().tolist()
    beats = ms3_table.mc_onset.dropna().tolist()
    voice = ['N' if str(v) == 'nan' else v for v in ms3_table.voice.tolist()]
    time_signatures = ms3_table.timesig.tolist()
    ## sacar possibilities
    voice_measures = get_compases_per_possibility(list(set(voice)), measures, voice, beats, time_signatures)
    annotations_voice = {'Voice': voice.count(1), 'No_voice': voice.count(0)}
    voice_measures['Voice'] = voice_measures.pop(1) if 1 in voice_measures else 0
    voice_measures['No_voice'] = voice_measures.pop(0) if 0 in voice_measures else 0

    # measures_section = get_compases_per_possibility(sections, measures, sections, beats, time_signatures)
    # annotations_sections = {k:sections.count(k) for k in measures_section}
    everything = dict(voice_measures)#, **measures_section)
    list_annotations = dict(annotations_voice)#, **annotations_sections)
    for k in everything:
        everything[k] = round(everything[k]/list_annotations[k] if list_annotations[k] != 0 else 0, 2)
    
    avg = sum(list(everything.values())) / (len(everything))
    
    return dict(everything, **{'Average': avg})

def get_chords(tabla_lausanne):
    chords = tabla_lausanne.chord.dropna().tolist()
    relativeroots = tabla_lausanne.relativeroot.tolist() 
    keys = tabla_lausanne.localkey.dropna().tolist() # TODO: comprobar en el 'enunciado' que en Chords hay que obtener la local key y no la global

    cg1, cg2 = get_chords_functions(chords, relativeroots, keys)
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
    form_l = make_type_col(tabla_lausanne)
        
    #convert the list of forms in their groups
    grouped_forms = get_chordtype_functions(form_l)

    form_counter = Counter(grouped_forms)
    fc = {}
    for f in form_counter:
        fc['Chord types' + str(f)] = str(round((form_counter[f] / sum(list(form_counter.values()))) * 100, 2)) + '%'
    return fc

def get_numerals(tabla_lausanne):
    numerals = tabla_lausanne.numeral.dropna().tolist()
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

    _, ng2 = get_numerals_function(numerals, relativeroots, keys)
    numerals_counter = Counter(ng2)
    
    nc = {}
    for n in numerals_counter:
        nc['Numerals'+str(n)] = str(round((numerals_counter[n]/sum(list(numerals_counter.values()))) * 100, 2)) + '%'
    return nc 

def get_modulations(tabla_lausanne, sections, major = True):
    keys = tabla_lausanne.localkey.dropna().tolist()
    grouping, _ = get_keys_functions(keys, mode = 'M' if major else 'm')
    modulations_sections = {g:[] for g in grouping}
    # Count the number of sections in each key
    last_key = ''
    for i, k in enumerate(keys):
        if (k.lower() != 'i') and k != last_key: #premisa
            # section = sections[i] #??? NON comprendo
            last_key = k
            modulation = grouping[i]
            # modulations_sections[modulation].append(section)
        # if last_key == k and sections[i] != section:
        #     section = sections[i]
        #     modulations_sections[modulation].append(section)
    
    #borramos las modulaciones con listas vacías y dejamos un counter en vez de una lista
    ms = {}
    # for m in modulations_sections:
    #     if len(modulations_sections[m]) != 0:
    #         ms['Modulations'+str(m)] = len(list(set(modulations_sections[m])))
    # return ms

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

def get_harmony_data(score_data: dict, harmonic_analysis: DataFrame, sections: list = None) -> dict:
    hr = get_harmonic_rhythm(harmonic_analysis, sections)
    harmonic_rhythm = {'Harmonic rhythm_'+k: hr[k] for k in hr}

    # 2. Modulations TODO: revisar 
    ### DEPENDE DE SECTIONS Y NO TENEMOS YET
    modulations = get_modulations(harmonic_analysis, sections, major = score_data['mode'] == 'major')
    
    # 3. Numerals
    numerals = get_numerals(harmonic_analysis)
    # 4. Chord_types
    chord_types = get_chord_types(harmonic_analysis) 
    # 5. Additions
    # additions = get_additions(harmonic_analysis)

    # key_name = score_data['key'].split(" ")[0].strip().replace('-','b') #coger solo la string de antes del espacio? y así quitar major y minor
    # key_name = key_name if score_data['mode'] == 'major' else key_name.lower()
    # score_data['key'] = key_name

    return dict(score_data, **harmonic_rhythm, **numerals)#, **modulations, , **chord_types, **additions)
def expand_repeat_bars(score):
    final_score = m21.stream.Score()
    final_score.metadata = score.metadata
    exist_repetition_bars = False
    #find repeat bars and expand
    for instr in score.parts:
        part_measures = get_instrument_elements(instr.elements) #returns the measures with repetitions
        last_measure = part_measures[-1].measureNumber
        part_measures_expanded = []
        startsin0 = part_measures[0].measureNumber == 0 #Everything should be -1
        repetition_bars = []

        #Find all repetitions in that instrument
        for elem in instr.elements:
            if isinstance(elem, m21.stream.Measure):
                for e in elem:
                    if isinstance(e, m21.bar.Repeat):
                        exist_repetition_bars = True
                        if e.direction == "start":
                            repetition_bars.append((e.measureNumber, "start"))
                        elif e.direction == "end":
                            repetition_bars.append((e.measureNumber, "end"))
                        index = elem.elements.index(e)
                        elem.elements = elem.elements[:index] + elem.elements[index + 1:]
            elif isinstance(elem, m21.spanner.RepeatBracket):
                string_e = str(elem)
                index = string_e.find("music21.stream.Measure")
                measure = string_e[index:].replace("music21.stream.Measure", '')[1:3].strip()
                repetition_bars.append((int(measure), elem.number))
                index = instr.elements.index(elem)
                elem.elements = instr.elements[:index] + instr.elements[index + 1:]
        repetition_bars = sorted(list(repetition_bars), key=lambda tup:tup[0])

        start = 0 if startsin0 else 1
        if exist_repetition_bars:
            p = m21.stream.Part()
            p.id = instr.id
            p.partName = instr.partName
            for rb in repetition_bars:
                compass = measure_ranges(part_measures, rb[0], rb[0])[0].quarterLength
                if rb[1] == "start":
                    if len(part_measures_expanded) > 0:
                        offset = part_measures_expanded[-1][-1].offset
                    else:
                        offset = 0
                    start_measures = measure_ranges(part_measures, start, rb[0] - 1, offset = offset + compass) #TODO works if the score doesn't start in 0?
                    if len(start_measures) > 0:
                        part_measures_expanded.append(start_measures)
                    start = rb[0]
                elif rb[1] == "end":
                    if len(part_measures_expanded) > 0:
                        offset = part_measures_expanded[-1][-1].offset
                    else:
                        offset = 0
                    casilla_1 = True if any(re[1] == '1' and re[0] <= rb[0] for re in repetition_bars) else False
                    casilla_2 = None
                    if casilla_1:
                        casilla_2 = [re for re in repetition_bars if re[1] == '2' and re[0] > rb[0]]
                        casilla_2 = None if len(casilla_2) == 0 else casilla_2[0] 
                    part_measures_expanded.append(measure_ranges(part_measures, init = start, end = rb[0], offset = offset+ compass, remove_repetition_marks=True)) # This should erase the repetition marks
                    if casilla_2 is not None:
                        part_measures_expanded.append(measure_ranges(part_measures, start, casilla_2[0], iteration = 2, offset = part_measures_expanded[-1][-1].offset+ compass))
                        start = casilla_2[0] + 1
                    else:
                        part_measures_expanded.append(measure_ranges(part_measures, init = start, end = rb[0], offset = part_measures_expanded[-1][-1].offset + compass))
                        start = rb[0] + 1
            if start < last_measure:
                compass = measure_ranges(part_measures, start, start + 1)[0].quarterLength
                offset = part_measures_expanded[-1][-1].offset
                part_measures_expanded.append(measure_ranges(part_measures, start, last_measure + 1, offset = offset+ compass)) #TODO works when it's close to the end?

            p.elements = list(itertools.chain(*tuple(part_measures_expanded)))
            final_score.insert(0, p)
        
    return final_score if exist_repetition_bars else score

def expand_part(part, repeat_elements):
    part_measures = get_instrument_elements(part.elements) #returns the measures with repetitions
    p = m21.stream.Part()
    p.id = part.id
    p.partName = part.partName
    
    part_measures_expanded = get_measure_list(part_measures, repeat_elements) #returns the measures expanded
    part_measures_expanded = list(itertools.chain(*part_measures_expanded))
    #part_measures_expanded = sorted(tuple(part_measures_expanded), key =lambda x: x.offset)
    # Assign a new continuous compass number to every measure
    measure_number = 0 if part_measures_expanded[0].measureNumber == 0 else 1
    for i, e in enumerate(part_measures_expanded):
        m = m21.stream.Measure(number = measure_number)
        m.elements = e.elements
        m.offset  = e.offset
        m.quarterLength = e.quarterLength
        part_measures_expanded[i] = m
        measure_number += 1
    p.elements = part_measures_expanded
    return p

def expand_score_repetitions(score, repeat_elements):
    score = expand_repeat_bars(score) # FIRST EXPAND REPEAT BARS
    final_score = stream.Score()
    final_score.metadata = score.metadata
    
    if len(repeat_elements) > 0:
        for part in score.parts:
            p = expand_part(part, repeat_elements)

            final_score.insert(0, p)
    else:
        final_score = score
    return final_score

def parse_score(mscx_file: str):
    harmonic_analysis = None
    msc3_score = ms3.score.MSCX(mscx_file, level = 'c')
    has_table = True
    try:
        harmonic_analysis = msc3_score.expanded
    except Exception as e:
        has_table = False

    return msc3_score, harmonic_analysis, has_table

def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    global logger
    logger = cfg.read_logger
    features={}    
    try:
        #### GET FILE FROM LAUSSANE OR FROM MODULATIONS IN THE JSON_DATA ####
        # modulations = json_data['Modulations'] if 'Modulations' in json_data and len(json_data['Modulations']) != 0 else None
        # gv = dict(name_variables, **excel_variables, **general_variables, **grouped_variables, **scoring_variables, **clef_dic, **total) 
        if 'mscx_path' in score_data:
                try:                
                    path=score_data['mscx_path']

                    # This takes a while!!
                    msc3_score, harmonic_analysis, has_table = parse_score(path)

                    has_table = True

                except:
                    has_table = False
        else:
            pass
        # elif modulations is not None: # The user may have written only the not-expanded version
        #     has_table = True

        #     if modulations is not None and harmonic_analysis is None:
        #         harmonic_analysis = compute_modulations(partVoice, partVoice_expanded, modulations) #TODO: Ver qué pasa con par voice y como se puede hacer con la info que tenemos
        # #         pass
            
        score = score_data['score']
        repeat_elements= score_data['repetition_elements']
        score_prefix = get_score_prefix()
            # Obtain score sections:
            # sections = musical_form.get_form_measures(score, repeat_elements) #TODO: prove functionality
        sections=[]
        #     Get the array based on harmonic_analysis.mc
        # sections = continued_sections(sections, harmonic_analysis.mc)

            ################
            # HARMONY DATA #
            ################
        
        all__harmonic_info = get_harmony_data(score_data, harmonic_analysis, sections)
        
            # #############
            # # KEY AREAS #
            # #############

        keyareas = get_keyareas(harmonic_analysis, sections, major = score_data['mode'] == 'major')

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

        #Harmonic Rhythm
        features[f"{score_prefix}{HARMONIC_RHYTHM_VOICE}"] = all__harmonic_info['Harmonic rhythm_Voice']
        features[f"{score_prefix}{HARMONIC_RHYTHM_NOVOICE}"] = all__harmonic_info['Harmonic rhythm_No_voice']
        features[f"{score_prefix}{HARMONIC_RHYTHM_AVERAGE}"] = all__harmonic_info['Harmonic rhythm_Average']
        
        #NUMERALS
        features[f"{score_prefix}{NUMERALS_T}"] = all__harmonic_info['NumeralsT']
        features[f"{score_prefix}{NUMERALS_D}"] = all__harmonic_info['NumeralsD']
        features[f"{score_prefix}{NUMERALS_SD}"] = all__harmonic_info['NumeralsSD']
        features[f"{score_prefix}{NUMERALS_sharp_LN}"] = all__harmonic_info['Numerals#LN']
        features[f"{score_prefix}{NUMERALS}"] = all__harmonic_info['Numerals']
        
        #KEY AREAS
        features.update({k:v for (k, v) in keyareas.items()})
        
    except Exception as e:
            logger.error('Harmony problem found: ', exc_info=True)
            features={}

    return features
