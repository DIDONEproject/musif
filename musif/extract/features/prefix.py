from musif.extract.constants import DATA_PART_ABBREVIATION, DATA_SOUND_ABBREVIATION


def get_part_prefix(part_abbreviation: str) -> str:
    """
    Returns prefix name for a specific part given instrument's abbreviation

    Example
    'vnI' -> 'PartVnI_'

    Parameters
    ----------
    part_abbreviation:  str
        String that represents the abbreviated name of an instrument
    """
    if part_abbreviation is None or len(part_abbreviation) == 0:
        return "Part"
    return f"Part{part_abbreviation[0].upper() + part_abbreviation[1:]}_"


def get_sound_prefix(sound_abbreviation: str) -> str:
    """
    Returns prefix name for a specific part given sound's abbreviation

    Example
    'vnI' -> 'SoundVn_'

    Parameters
    ----------
    part_abbreviation:  str
        String that represents the abbreviated name of a sound
    """
    if sound_abbreviation is None or len(sound_abbreviation) == 0:
        return "Sound"
    return f"Sound{sound_abbreviation[0].upper() + sound_abbreviation[1:]}_"


def get_family_prefix(family_abbreviation: str) -> str:
    """
    Returns prefix name for a specific part given sound's abbreviation

    Example
    'vnI' -> 'SoundVn_'

    Parameters
    ----------
    part_abbreviation:  str
        String that represents the abbreviated name of a sound
    """

    if family_abbreviation is None or len(family_abbreviation) == 0:
        return "Family"
    return f"Family{family_abbreviation[0].upper() + family_abbreviation[1:]}_"


def get_score_prefix() -> str:
    return "Score_"


def get_corpus_prefix() -> str:
    return "Corpus_"


def get_part_feature(part: str, feature: str) -> str:
    """
    It builds the name of a feature with part scope.
    For instance, if the feature is "NumberOfIntervals" and the part is "VnI",
    this class would return: "PartVnI_NumberOfIntervals".
    Args:
        part (str): The part name.
        feature (str): Name of the feature to be prefixed.
    Returns:
        str: The feature properly prefixed for the part passed as argument.
    """

    return get_part_prefix(part) + feature


def get_sound_feature(sound: str, feature: str) -> str:
    """
    It builds the name of a feature with sound scope.

    For instance, if the feature is "NumberOfIntervals" and the sound is "Ob",
    this class would return: "SoundOb_NumberOfIntervals".

    Args:
        sound (str): The sound name.
        feature (str): Name of the feature to be prefixed.

    Returns:
        str: The feature properly prefixed for the sound passed as argument.
    """
    return get_sound_prefix(sound) + feature


def get_family_feature(family: str, feature: str) -> str:
    """
    It builds the name of a feature with family scope.

    For instance, if the feature is "NumberOfIntervals" and the family is "Str",
    this class would return: "FamilyStr_NumberOfIntervals".

    Args:
        family (str): The family name.
        feature (str): Name of the feature to be prefixed.

    Returns:
        str: The feature properly prefixed for the family passed as argument.
    """
    return get_family_prefix(family) + feature


def get_score_feature(feature: str) -> str:
    """
    It builds the name of a feature with Score scope.

    For instance, if the feature is "NumberOfIntervals",
    this class would return: "Score_NumberOfIntervals".

    Args:
        feature (str): Name of the feature to be prefixed.

    Returns:
        str: The feature properly prefixed for score scope.
    """
    return get_score_prefix() + feature
