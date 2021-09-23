from collections import Counter
from functools import lru_cache
from typing import List

import ms3
import pandas as pd

from musif.common.constants import RESET_SEQ, get_color
from musif.config import Configuration
from musif.extract.features.prefix import get_score_prefix
from pandas import DataFrame

from .__harmony_utils import (get_chord_types, get_chords, get_keyareas,
                              get_numerals, get_harmonic_rhythm, get_additions)

from .__constants import *


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
        if harmonic_analysis:

            ################
            # HARMONY DATA #
            ################
            
            all_harmonic_info = get_harmony_data(score_data, harmonic_analysis)
            
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
        
    except Exception as e:
        cfg.read_logger.error('Harmony problem found: ', e)
    
    finally:
        score_features.update(features)
    

def update_part_objects(score_data, part_data, _cfg, part_features):
    pass