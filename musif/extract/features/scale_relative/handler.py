from typing import List

from musif.config import Configuration
from musif.extract.common import filter_parts_data
from musif.extract.constants import DATA_PART_ABBREVIATION
from musif.extract.features.prefix import get_part_prefix
from musif.extract.features.scale_relative.utils import get_emphasised_scale_degrees_relative
from musif.logs import lerr
from .constants import *


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    if 'MS3_score' in score_data:
        try:
            notes_per_degree_relative = get_emphasised_scale_degrees_relative(part_data['notes'], score_data)
            all_degrees = sum(value for value in notes_per_degree_relative.values())

            for key, value in notes_per_degree_relative.items():
                part_features[DEGREE_COUNT.format(key=key, prefix="")] = value
                part_features[DEGREE_PER.format(key=key, prefix="")] = value / all_degrees if all_degrees != 0 else 0
        except Exception as e:
            lerr(f'Error extracting relative scale degrees: {str(e)}')


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):
    parts_data = filter_parts_data(parts_data, cfg.parts_filter)
    
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
