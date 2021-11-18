from musif.extract.constants import DATA_PART_ABBREVIATION


def get_part_prefix(part_abbreviation: str) -> str:
    return f"Part{part_abbreviation[0].upper() + part_abbreviation[1:]}_"


def get_family_prefix(family_abbreviation: str) -> str:
    return f"Family{family_abbreviation[0].upper() + family_abbreviation[1:]}_"


def get_score_prefix() -> str:
    return "Score_"


def get_corpus_prefix() -> str:
    return "Corpus_"


def part_feature_name(part_data: dict, feature: str) -> str:
    part_abbreviation = part_data[DATA_PART_ABBREVIATION]
    return get_part_prefix(part_abbreviation) + feature


def get_family_feature(family: str, feature: str) -> str:
    return get_family_prefix(family) + feature


def score_feature_name(feature: str) -> str:
    return get_score_prefix() + feature


