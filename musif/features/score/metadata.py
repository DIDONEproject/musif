from config import scores_metadata


def merge_metadata_features(features: dict, metadata_features: dict, strategy: str = "unique") -> dict:
    metadata_features = {}
    for file_name, metadata in scores_metadata:
        for key, value in metadata:
            if key in features:
                if strategy == "unique":
                    continue
                else:
                    effective_key = file_name.capitalize() + key.capitalize()
            else:
                effective_key = key.capitalize()
            metadata_features[effective_key] = value
    return metadata_features