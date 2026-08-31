from typing import List

import music21 as m21
from music21.features import native
from music21.features.base import extractorsById

from musif import cache
from musif.config import ExtractConfiguration
from musif.extract.constants import DATA_SCORE

from .constants import EXCLUDED_FEATURES_IDS


def allFeaturesAsList(cfg, streamInput):
    """
    only a little change around m21.features.base.allFeaturesAsList: no Parallel
    processing
    """

    ds = m21.features.base.DataSet(classLabel="")
    ds.runParallel = False  # this is the only difference with the m21 original code
    final_features = [
        feature
        for feature in native.featureExtractors
        if feature.id not in EXCLUDED_FEATURES_IDS
    ]
    ds.addFeatureExtractors(final_features)
    ds.addData(streamInput)
    ds.process()
    allData = ds.getFeaturesAsList(
        includeClassLabel=False, includeId=False, concatenateLists=False
    )
    # with those flags getFeaturesAsList returns the single row: one vector
    # per extractor, aligned with final_features
    assert len(allData) == len(final_features), (
        "music21 features misaligned with their extractors"
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
