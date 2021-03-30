def get_part_prefix(part_abbreviation: str) -> str:
    return f"Part{part_abbreviation[0].upper() + part_abbreviation[1:]}"


def get_sound_prefix(sound_abbreviation: str) -> str:
    return f"Sound{sound_abbreviation[0].upper() + sound_abbreviation[1:]}"


def get_family_prefix(family_abbreviation: str) -> str:
    return f"Family{family_abbreviation[0].upper() + family_abbreviation[1:]}"


def get_score_prefix() -> str:
    return "Score"



