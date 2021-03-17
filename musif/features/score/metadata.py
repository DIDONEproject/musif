from musif.config import Configuration


def get_metadata_features(file_name: str, existing_features: dict, config: Configuration) -> dict:
    metadata = config.scores_metadata.get(file_name)
    if not metadata:
        return {}
    for key in metadata.keys():
        if key in existing_features:
            config.read_logger.warning(f"Duplicated feature '{key}' was found in file '{file_name}' and will be skipped.")
    return metadata
