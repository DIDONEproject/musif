from musif.extract.features.custom.__constants import ADDITIONS_prefix, CHORD_TYPES_prefix, CHORD_prefix, NUMERALS_prefix
from typing import List

from pandas import DataFrame

from musif.config import Configuration
from musif.extract.features.core import DATA_MODE
from .__constants import *
from .__harmony_utils import (get_additions, get_chord_types, get_chords, get_harmonic_rhythm, get_keyareas,
                              get_numerals)


def get_harmony_data(score_data: dict, harmonic_analysis: DataFrame) -> dict:
    
    # 1. Harmonic_rhythm
    harmonic_rhythm = get_harmonic_rhythm(harmonic_analysis)

    # 2. Numerals
    numerals = get_numerals(harmonic_analysis)
    
    # 3. Chord_types
    chord_types = get_chord_types(harmonic_analysis) 
    
    # 4. Additions
    additions = get_additions(harmonic_analysis)

    return dict( **harmonic_rhythm, **numerals, **chord_types, **additions)#, **modulations) #score_data was also returned before

def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):
    features={}
    try:

        harmonic_analysis=score_data['MS3_score'] if 'MS3_score' in score_data else None

    #     Get the array based on harmonic_analysis.mc
        # sections = continued_sections(sections, harmonic_analysis.mc)
        if not harmonic_analysis.empty:

            ################
            # HARMONY DATA #
            ################
            
            all_harmonic_info = get_harmony_data(score_data, harmonic_analysis)
            
            # #############
            # # KEY AREAS #
            # #############

            keyareas = get_keyareas(harmonic_analysis, major = score_data[DATA_MODE] == 'major')

            # #############
            # #  CHORDS   #
            # #############

            chords, chords_grouping1, chords_grouping2 = get_chords(harmonic_analysis)

            #HARMONIC RHYTHM
            features[f"{HARMONIC_RHYTHM}"] = all_harmonic_info[HARMONIC_RHYTHM]
            features[f"{HARMONIC_RHYTHM_BEATS}"] = all_harmonic_info[HARMONIC_RHYTHM_BEATS]
            
            #NUMERALS
            features.update({k:v for (k, v) in all_harmonic_info.items() if k.startswith(NUMERALS_prefix)})
            
            # KEY AREAS
            features.update({k:v for (k, v) in keyareas.items()})
            
            # CHORD TYPES
            features.update({k:v for (k, v) in all_harmonic_info.items() if k.startswith(CHORD_TYPES_prefix)})
            
            #CHORDS
            features.update({k:v for (k, v) in chords.items() if k.startswith(CHORD_prefix)})
            features.update({k:v for (k, v) in chords_grouping1.items() if k.startswith(CHORDS_GROUPING_prefix)})
            features.update({k:v for (k, v) in chords_grouping2.items() if k.startswith(CHORDS_GROUPING_prefix)})

            # ADDITIONS
            features.update({k:v for (k, v) in all_harmonic_info.items() if k.startswith(ADDITIONS_prefix)})
        
    except Exception as e:
        cfg.read_logger.error('Harmony problem found: ', e)
    
    finally:
        score_features.update(features)
    

def update_part_objects(score_data, part_data, _cfg, part_features):
    pass