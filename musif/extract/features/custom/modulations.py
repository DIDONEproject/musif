from typing import List
from music21.note import Note

import pandas as pd
from musif.config import Configuration
from .__modulations_utils import get_modulations, IsAnacrusis, get_localTonalty, get_note_degree, get_tonality_for_measure

accidental_abbreviation = {"": "", "sharp": "#", "flat": "b", "double-sharp": "x", "double-flat": "bb"}

DEGREE_COUNT = "{prefix}Degree{key}_Count_relative"
DEGREE_PER = "{prefix}Degree{key}_Per_relative"

##########################################################################################
# Transforms the list of notes into their scale degrees, based on the local key          #
##########################################################################################

def get_emphasised_scale_degrees_relative(notes_list: list, score_data: dict) -> List[list]:
    harmonic_analysis=score_data['MS3_score']
    tonality=score_data['tonality']
    notes_measures = []
    renumbered_measures = harmonic_analysis.mc.dropna().tolist()

    for n in notes_list:
        notes_measures.append((n.name, n.measureNumber))


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
    for n in notes_list:
        note_name = n.name
        note_measure = n.measureNumber
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

def update_part_objects(score_data, part_data, cfg, part_features):
    
    try:
        notes_per_degree_relative, error_compasses = get_emphasised_scale_degrees_relative(part_data['notes'], score_data)
        all_degrees = sum(value for value in notes_per_degree_relative.values())

        for key, value in notes_per_degree_relative.items():
            part_features[DEGREE_COUNT.format(key=key, prefix="")] = value
            part_features[DEGREE_PER.format(key=key, prefix="")] = value / all_degrees if all_degrees != 0 else 0
    
    except Exception as e:
        cfg.read_logger.error('Modulations error found: {}', e)
###############################################################################
# This function generates a dataframe with the measures and the local key     #
# present in each one of them based on the 'modulations' atribute in the json #
# ###############################################################################
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
        
def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):
    features={}
    sections=[]
    try:
        #tenemos lista de notas aqui para hacer emph degrees b???
        
        harmonic_analysis=score_data['MS3_score']
        
        modulations = get_modulations(harmonic_analysis, sections, major = score_data['mode'] == 'major')
        emph_degrees, _= get_emphasised_scale_degrees_relative(score_data)
        # elif modulations is not None: # The user may have written only the not-expanded version

        #     if modulations is not None and harmonic_analysis is None:
        #         harmonic_analysis = compute_modulations(partVoice, partVoice_expanded, modulations) #TODO: Ver qué pasa con par voice y como se puede hacer con la info que tenemos
        # #         pass
                    # Obtain score sections:
                    # sections = musical_form.get_form_measures(score, repeat_elements) #TODO: prove functionality

    except Exception as e:
        cfg.read_logger.error('Modulations problem found: ', e)

