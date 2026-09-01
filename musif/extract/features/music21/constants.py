# music21 native extractors excluded from extraction. P22 (QualityFeature)
# duplicated the Mode feature (0/1 major-minor), crashed under the
# SmartModuleCache wrapper (so cached and cache-less runs disagreed on the
# column set), and music21 itself documents it as unreliable - dropped.
EXCLUDED_FEATURES_IDS = [
    "P22",  # QualityFeature
]
