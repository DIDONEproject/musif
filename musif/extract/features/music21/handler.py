from typing import List

import music21 as m21
from music21.features import jSymbolic, native
from music21.features.base import extractorsById

from musif import cache
from musif.config import ExtractConfiguration
from musif.extract.constants import DATA_SCORE
from .constants import ERRORED_NAMES


def allFeaturesAsList(streamInput, includeJSymbolic=True):
    """
    only a little change around m21.features.base.allFeaturesAsList: no Parallel
    processing
    """

    ds = m21.features.base.DataSet(classLabel="")
    ds.runParallel = False  # this is the only difference with the m21 original code
    all_features = list(native.featureExtractors)
    if includeJSymbolic:
        all_features += list(jSymbolic.featureExtractors)
    f = [feature for feature in all_features if feature.id not in
         ERRORED_NAMES]
    # f = list(native.featureExtractors)
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
    # avoid extracting jsymbolic features twice
    includeJSymbolic = 'jsymbolic' in cfg.features
    features = allFeaturesAsList(score, includeJSymbolic=includeJSymbolic)
    if includeJSymbolic:
        all_columns = [x.id for x in extractorsById("all")]
    else:
        all_columns = [x.id for x in extractorsById("native")]
    columns = [c for c in all_columns if c not in ERRORED_NAMES]
    score_features.update(
        {
            'm21_' + columns[outer] + f"_{i}": f
            for outer in range(len(columns))
            for i, f in enumerate(features[outer])
        }
    )


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    pass
