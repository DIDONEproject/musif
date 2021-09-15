from functools import lru_cache
from typing import List

import ms3
import pandas as pd
from pandas import DataFrame

from musif.common.constants import RESET_SEQ, get_color
from musif.config import Configuration
from musif.extract.features.prefix import get_score_prefix
from .__harmony_utils import (get_chord_types, get_chords, get_keyareas,
                              get_numerals, get_harmonic_rhythm, get_additions, HARMONIC_RHYTHM, HARMONIC_RHYTHM_BEATS)

ALPHA = "abcdefghijklmnopqrstuvwxyz"


###############################################################################
# This function generates a dataframe with the measures and the local key     #
# present in each one of them based on the 'modulations' atribute in the json #
# ###############################################################################
# def compute_modulations(partVoice, partVoice_expanded, modulations):
#     try:
#         measures = [m.measureNumber for m in partVoice]
#         measures_expanded = [m.measureNumber for m in partVoice_expanded]
        
#         first_modulation = modulations[0]
#         key = []
#         for m in modulations[1:]:
#             key += [first_modulation[0]] * measures.index(m[1] - first_modulation[1] + 1)
#             first_modulation = m
#         key += [first_modulation[0]] * (measures[-1] - first_modulation[1] + 1)
#         if measures[-1] != measures_expanded[-1]: #there are repetitions TODO: test
#             measures_expanded = measures_expanded[measures_expanded.index(measures[-1]):] #change the starting point
#             first_modulation = modulations[0]
#             for m in modulations[1:]:
#                 if m[1] <= len(measures_expanded):
#                     key += [first_modulation[0]] * measures_expanded.index(m[1] - first_modulation[1] + 1)
#                     first_modulation = m
#         return pd.DataFrame({'measures_continued': measures_expanded, 'key': key})
#     except:
#         print('Please, review the format of the modulation\'s indications in the JSON file. It needs to have the following format: [(<local key>, <starting measure>), ... ]')
#         return None

def get_harmony_data(score_data: dict, harmonic_analysis: DataFrame, sections: list = None) -> dict:
    
    # 1. Harmonic_rhythm
    harmonic_rhythm = get_harmonic_rhythm(harmonic_analysis, sections)

    # 2. Modulations TODO: revisar 
    ### --- DEPENDE DE SECTIONS Y NO TENEMOS YET ---
    # modulations = get_modulations(harmonic_analysis, sections, major = score_data['mode'] == 'major')
    
    # 3. Numerals
    numerals = get_numerals(harmonic_analysis)
    
    # 4. Chord_types
    chord_types = get_chord_types(harmonic_analysis) 
    
    # 5. Additions
    additions = get_additions(harmonic_analysis)

    # key_name = str(score_data['key']).split(" ")[0].strip().replace('-','b') #coger solo la string de antes del espacio? y así quitar major y minor
    # key_name = key_name if score_data['mode'] == 'major' else key_name.lower()
    # score_data['key'] = key_name

    return dict( **harmonic_rhythm, **numerals, **chord_types, **additions)#, **modulations) #score_data was also returned before


@lru_cache(maxsize=None, typed=False)
def parse_score(mscx_file: str, cfg: Configuration):
    # mscx_file=mscx_file.replace(' ', '')
    harmonic_analysis = None
    # annotations=msc3_score.annotations
    has_table = True
    try:
        cfg.read_logger.info(get_color('INFO')+'\nGetting harmonic analysis...{0}'.format(mscx_file) + RESET_SEQ)
        print('\nGetting harmonic analysis...{0}'.format(mscx_file))
        msc3_score = ms3.score.Score(mscx_file, logger_cfg={'level': 'ERROR'})
        harmonic_analysis = msc3_score.mscx.expanded

        #AQUI EMPIEZA LA FIESTA
        if harmonic_analysis is None:
            raise Exception('Not able to extract chords from the .mscx file!')
        mn = ms3.parse.next2sequence(msc3_score.mscx.measures.set_index('mc').next)
        mn = pd.Series(mn, name='mc_playthrough')
        harmonic_analysis = ms3.parse.unfold_repeats(harmonic_analysis,mn)
    
    except Exception as e:
        cfg.read_logger.error(get_color('ERROR')+'An error occurred parsing the score {}: {}{}'.format(mscx_file,e, RESET_SEQ))
        with open('failed_files.txt', 'a') as file:  # Use file to refer to the file object
            file.write(str(mscx_file) + '\n')

        harmonic_analysis_expanded = None
        has_table = False

    return harmonic_analysis, has_table

def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    features={}
    sections=[]
    try:
        #### GET FILE FROM LAUSSANE OR FROM MODULATIONS IN THE JSON_DATA ####
        # modulations = json_data['Modulations'] if 'Modulations' in json_data and len(json_data['Modulations']) != 0 else None
        # gv = dict(name_variables, **excel_variables, **general_variables, **grouped_variables, **scoring_variables, **clef_dic, **total) 
        if 'mscx_path' in score_data:
            path=score_data['mscx_path']
            # This takes a while!!
            harmonic_analysis, has_table = parse_score(path, cfg)
            # print("Time taken to execute the function without lru_cache is: ", end-begin)

            has_table = True

        # elif modulations is not None: # The user may have written only the not-expanded version
        #     has_table = True

        #     if modulations is not None and harmonic_analysis is None:
        #         harmonic_analysis = compute_modulations(partVoice, partVoice_expanded, modulations) #TODO: Ver qué pasa con par voice y como se puede hacer con la info que tenemos
        # #         pass
                    # Obtain score sections:
                    # sections = musical_form.get_form_measures(score, repeat_elements) #TODO: prove functionality
            
            score = score_data['score']
            repeat_elements= score_data['repetition_elements']
            score_prefix = get_score_prefix()

        else:
            has_table = False
            harmonic_analysis = None
            cfg.read_logger.warn(get_color('WARNING')+'No Musescore file was found.'+ RESET_SEQ)
            return {}

        #     Get the array based on harmonic_analysis.mc
        # sections = continued_sections(sections, harmonic_analysis.mc)
        if harmonic_analysis is not None:
            ################
            # HARMONY DATA #
            ################
            
            all_harmonic_info = get_harmony_data(score_data, harmonic_analysis, sections)
            
            # #############
            # # KEY AREAS #
            # #############

            keyareas = get_keyareas(harmonic_analysis, major = score_data['mode'] == 'major')

            # #############
            # #  CHORDS   #
            # #############

            chords, chords_g1, chords_g2 = get_chords(harmonic_analysis)

            ## COLLECTING FEATURES 

            #Harmonic Rhythm
            features[f"{HARMONIC_RHYTHM}"] = all_harmonic_info[HARMONIC_RHYTHM]
            features[f"{HARMONIC_RHYTHM_BEATS}"] = all_harmonic_info[HARMONIC_RHYTHM_BEATS]
            
            #NUMERALS
            features.update({k:v for (k, v) in all_harmonic_info.items() if k.lower().startswith('numerals')})
            
            # KEY AREAS
            features.update({k:v for (k, v) in keyareas.items()})
            
            # CHORD TYPES
            features.update({k:v for (k, v) in all_harmonic_info.items() if k.startswith('chord_types_')})
            
            #CHORDS
            features.update({k:v for (k, v) in chords.items() if k.startswith('chords_')})
            features.update({k:v for (k, v) in chords_g1.items() if k.startswith('chords_')})
            features.update({k:v for (k, v) in chords_g2.items() if k.startswith('chords_')})

            # ADDITIONS
            features.update({k:v for (k, v) in all_harmonic_info.items() if k.startswith('additions_')})
        return features

    except Exception as e:
        cfg.read_logger.error('Harmony problem found: ', e)
        return features

def get_part_features(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict) -> dict:
    return {}
