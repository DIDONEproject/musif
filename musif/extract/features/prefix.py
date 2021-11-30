from musif.extract.constants import DATA_PART_ABBREVIATION


def get_part_prefix(part_abbreviation: str) -> str:
    if part_abbreviation is None or len(part_abbreviation) == 0:
        return "Part"
    return f"Part{part_abbreviation[0].upper() + part_abbreviation[1:]}_"


def get_sound_prefix(sound_abbreviation: str) -> str:
    if sound_abbreviation is None or len(sound_abbreviation) == 0:
        return "Sound"
    return f"Sound{sound_abbreviation[0].upper() + sound_abbreviation[1:]}_"


def get_family_prefix(family_abbreviation: str) -> str:
    if family_abbreviation is None or len(family_abbreviation) == 0:
        return "Family"
    return f"Family{family_abbreviation[0].upper() + family_abbreviation[1:]}_"


def get_score_prefix() -> str:
    return "Score_"


def get_corpus_prefix() -> str:
    return "Corpus_"


def part_feature_name(part_data: dict, feature: str) -> str:
    """
    It builds the name of a feature for a specific part, prefixing the feature name
    with the part abbreviation prefix.

    For instance, if the feature is "NumberOfIntervals" and the part abbreviation is "ObI",
    this class would return: "PartObI_NumberOfIntervals".

    Args:
        part_data (dict): A dictionary containing the data part abbreviation.
        feature (str): Name of the feature to be prefixed.

    Returns:
        str: The feature properly prefixed for the part passed as argument.
    """
    part_abbreviation = part_data[DATA_PART_ABBREVIATION]
    return get_part_prefix(part_abbreviation) + feature


def get_family_feature(family: str, feature: str) -> str:
    return get_family_prefix(family) + feature


def score_feature_name(feature: str) -> str:
    return get_score_prefix() + feature


