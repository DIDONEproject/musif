from typing import List

import music21 as m21
from music21.features import jSymbolic, native

from musif import cache
from musif.config import ExtractConfiguration
from musif.extract.constants import DATA_SCORE
from .constants import COLUMNS


import pickle
def allFeaturesAsList(streamInput):
    """
    only a little change around m21.features.base.allFeaturesAsList: no Parallel
    processing
    """

    ds = m21.features.base.DataSet(classLabel="")
    ds.runParallel = False  # this is the only difference with the m21 original code
    # f = list(jSymbolic.featureExtractors) + list(native.featureExtractors)
    f = list(native.featureExtractors)
    ds.addFeatureExtractors(f)
    ds.addData(streamInput)
    ds.process()
    allData = ds.getFeaturesAsList(
        includeClassLabel=False, includeId=False, concatenateLists=False
    )

    return allData


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    score = score_data[DATA_SCORE]
    # override the isinstance and hasattr definitions for the caching system
    m21.features.base.isinstance = cache.isinstance
    m21.features.base.hasattr = cache.hasattr
    features = allFeaturesAsList(score)
    score_features.update(
        {
            COLUMNS[outer] + f"_{i}": f
            for outer in range(len(COLUMNS))
            for i, f in enumerate(features[outer])
        }
    )


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    pass
