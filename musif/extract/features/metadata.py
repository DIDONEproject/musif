from typing import List

from config import Configuration


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    features = {}
    for group_name, group_features in cfg.scores_metadata.items():
        existing_metadata_id = score_features.get(cfg.metadata_id_col)
        if not existing_metadata_id:
            continue
        if len(group_features) == 0:
            continue
        if cfg.metadata_id_col not in group_features[0]:
            continue
        for item_features in group_features:
            if item_features[cfg.metadata_id_col] != existing_metadata_id:
                continue
            for key in item_features:
                if (key in score_features) and (key != cfg.metadata_id_col):
                    cfg.read_logger.warning(f"Column {key} exists both in metadata and in existing features")
                    continue
                features[key] = item_features[key]
    return features

