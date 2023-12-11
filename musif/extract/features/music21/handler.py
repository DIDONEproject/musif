from typing import List

import music21 as m21
from music21.features import native
from music21.features.base import extractorsById

from musif import cache
from musif.config import ExtractConfiguration
from musif.extract.constants import DATA_SCORE
from musif.logs import pwarn

from .constants import ERRORED_FEATURES_IDS


def allFeaturesAsList(cfg, streamInput):
    """
    only a little change around m21.features.base.allFeaturesAsList: no Parallel
    processing
    """

    ds = m21.features.base.DataSet(classLabel="")
    ds.runParallel = False  # this is the only difference with the m21 original code
    all_features = list(native.featureExtractors)
    if cfg.cache_dir:
        pwarn('\nCache is activated! Some music21 features will NOT be computed.')
        final_features = [feature for feature in all_features if feature.id not in
            ERRORED_FEATURES_IDS]
    else:
        final_features = all_features
    ds.addFeatureExtractors(final_features)
    ds.addData(streamInput)
    ds.process()
    allData = ds.getFeaturesAsList(
        includeClassLabel=False, includeId=False, concatenateLists=False
    )
    return allData, [c.__name__ for c in final_features]


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    score = score_data[DATA_SCORE]
    # Override the isinstance and hasattr definitions for the caching system
    m21.features.base.isinstance = cache.isinstance
    m21.features.base.hasattr = cache.hasattr
    features, columns = allFeaturesAsList(cfg, score)
    score_features.update(
        {
            'm21_' + columns[outer] + f"_{i}": f
            for outer in range(len(features))
            for i, f in enumerate(features[outer])
        }
    )

def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    pass
