def get_part_prefix(part_abbreviation: str) -> str:
    return f"Part{part_abbreviation[0].upper() + part_abbreviation[1:]}_"


def get_family_prefix(family_abbreviation: str) -> str:
    return f"Family{family_abbreviation[0].upper() + family_abbreviation[1:]}_"


def get_score_prefix() -> str:
    return "Score_"


def get_corpus_prefix() -> str:
    return "Corpus_"




