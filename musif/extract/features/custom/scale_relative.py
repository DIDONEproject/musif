from musif.common.constants import RESET_SEQ, get_color
from typing import List

import pandas as pd
from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.constants import DATA_PARTS_FILTER, DATA_PART_ABBREVIATION
from musif.extract.features.prefix import get_part_prefix

from .__scale_relative_utils import get_modulations, get_emphasised_scale_degrees_relative, continued_sections

accidental_abbreviation = {"": "", "sharp": "#", "flat": "b", "double-sharp": "x", "double-flat": "bb"}

DEGREE_COUNT = "{prefix}Degree{key}_Count_relative"
DEGREE_PER = "{prefix}Degree{key}_Per_relative"

def update_part_objects(score_data, part_data, cfg, part_features):
    
    try:
        notes_per_degree_relative = get_emphasised_scale_degrees_relative(part_data['notes'], score_data)
        all_degrees = sum(value for value in notes_per_degree_relative.values())

        for key, value in notes_per_degree_relative.items():
            part_features[DEGREE_COUNT.format(key=key, prefix="")] = value
            part_features[DEGREE_PER.format(key=key, prefix="")] = value / all_degrees if all_degrees != 0 else 0
    except Exception as e:
        cfg.read_logger.error('Error extracting relative scale degrees: {}', e)

def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):
    parts_data = filter_parts_data(parts_data, score_data[DATA_PARTS_FILTER])
    
    if len(parts_data) == 0:
        return

    for part_data, parts_features in zip(parts_data, parts_features):
        part_prefix = get_part_prefix(part_data[DATA_PART_ABBREVIATION])
        for feature in parts_features:
            if "Degree" in feature:
                score_features[f"{part_prefix}{feature}"] = parts_features[feature]
    
    

    ## MODULATIONS MODULE DISABLED AT THE MOMENT. t simplify things, we don't take modulations info into analysis and only Emphasized degrees relative
    
    # sections=[]

    # harmonic_analysis=score_data['MS3_score']
    # Obtain score sections:
    # sections = musical_form.get_form_measures(score, repeat_elements) #TODO: prove functionality
    # Get the array based on harmonic_analysis.mc
    # sections = continued_sections(sections, harmonic_analysis.mc)
    # modulations = get_modulations(harmonic_analysis, sections, major = score_data['mode'] == 'major')
