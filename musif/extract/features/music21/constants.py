# music21 native extractors that fail when the SmartModuleCache wraps the
# score, skipped when cache_dir is set. NOTE: with caching on, the m21_
# column set differs from a cache-less run by exactly these extractors.
ERRORED_FEATURES_IDS = [
    "P22",  # QualityFeature
]
