from typing import List

import pandas as pd
from musif.config import Configuration
from .__modulations_utils import get_modulations, get_emphasised_scale_degrees_relative, continued_sections

accidental_abbreviation = {"": "", "sharp": "#", "flat": "b", "double-sharp": "x", "double-flat": "bb"}

DEGREE_COUNT = "{prefix}Degree{key}_Count_relative"
DEGREE_PER = "{prefix}Degree{key}_Per_relative"

def update_part_objects(score_data, part_data, cfg, part_features):
    
    try:
        notes_per_degree_relative, error_measures = get_emphasised_scale_degrees_relative(part_data['notes'], score_data)
        all_degrees = sum(value for value in notes_per_degree_relative.values())
        if error_measures:
            cfg.read_logger.error(f'Some measures threw an error: {error_measures}')

        for key, value in notes_per_degree_relative.items():
            part_features[DEGREE_COUNT.format(key=key, prefix="")] = value
            part_features[DEGREE_PER.format(key=key, prefix="")] = value / all_degrees if all_degrees != 0 else 0
    
    except Exception as e:
        cfg.read_logger.error('Modulations error found: {}', e)

def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):
    features={}
    sections=[]
    try:
        harmonic_analysis=score_data['MS3_score']

        # Obtain score sections:
        # sections = musical_form.get_form_measures(score, repeat_elements) #TODO: prove functionality

        # Get the array based on harmonic_analysis.mc
        # sections = continued_sections(sections, harmonic_analysis.mc)
        modulations = get_modulations(harmonic_analysis, sections, major = score_data['mode'] == 'major')


    except Exception as e:
        cfg.read_logger.error('Modulations problem found: ', e)

