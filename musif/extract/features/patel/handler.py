import ipdb

from music21.analysis.patel import nPVI, melodicIntervalVariability

import musif.extract.constants as C
from musif.extract.features.prefix import get_part_feature
from musif.config import ExtractConfiguration
from typing import List


from musif.extract.features.patel.constants import *


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    # "update_part_objects from module inside a package given its parent package (score)!"
  
    for measure in part_data["measures"]:
        try:
            _nPVI = nPVI(measure)
            _melodicIntervalVariability = melodicIntervalVariability(measure)
        except Exception:
            _nPVI = 0.0
            _melodicIntervalVariability = 0.0

        # print('_nPVI: ', _nPVI)
        part_features['NPVI'] =  _nPVI

        # print('_melodicIntervalVariability: ', _melodicIntervalVariability)
        part_features['MIV'] =  _melodicIntervalVariability


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    # We need to add the data to score_features, 
    # the dictionary where all final info is stored. 
    # Otherwise it will not be reflected in the final dataframe.
    # "Updating stuffs from module inside a package  given its parent package (part)!"

    features = {}
    for part_data, part_features in zip(parts_data, parts_features):
        part_abbreviation = part_data[C.DATA_PART_ABBREVIATION]
        # get NPVI
        feature_name = get_part_feature(part_abbreviation, NPVI)
        features[feature_name] = part_features['NPVI']
        # get MIV
        feature_name = get_part_feature(part_abbreviation, MIV)
        features[feature_name] = part_features['MIV']

    score_features.update(features)




