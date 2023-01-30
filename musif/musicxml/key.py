from typing import Tuple

from music21.key import Key
from music21.stream.base import Score


def _get_key_signature(score_key: Key) -> str:
    """
    Returns the key signature from a specific music21 Key object

    Parameters
    ----------
        score_key : Key
        Music21 Key to take the info from
    """

    if score_key.sharps:
        key_signature = (
            "b" * abs(score_key.sharps)
            if score_key.sharps < 0
            else "s" * score_key.sharps
        )
    else:
        key_signature = "n"
    return key_signature


def get_key_signature_type(key_signature: str) -> str:
    """
    Returns the key signature type ('bb) for flats, 'ss' for sharps, and 'nn' for naturals

    Parameters
    ----------
        key_signature: str
            Music21 key to take the info from
    """
    return key_signature[0]


def get_key_and_mode(score: Score) -> Tuple[Key, str, str]:
    """
    Returns abbreviated designation of keys (uppercase for major mode; lowercase for minor mode)

    Example
    ----------
    if key == 'D- major': return 'Db'

    Parameters
    ----------
        score : Score
      Music21 score to take the info from
    """

    score_key = score.analyze("key")
    mode, tonality = get_name_from_key(score_key)
    return score_key, tonality, mode


def get_name_from_key(score_key: Key) -> Tuple[str, str]:
    """
    Returns abbreviated designation of keys (uppercase for major mode; lowercase for minor mode)

    Example
    ----------
    if key == 'D- major': return 'Db'

    Parameters
    ----------
        score : Score
            Music21 score to take the info from
    """

    key_parts = score_key.name.split(" ")
    mode = key_parts[1].strip().lower()
    tonality = key_parts[0]
    tonality = tonality.lower() if mode == "minor" else tonality.capitalize()
    tonality = tonality.replace("-", "b")
    return mode, tonality


def _get_key(score: Score) -> str:
    return str(score.analyze("key"))


def _get_mode(key: str) -> str:
    if key.isupper():
        return "M"
    else:
        return "m"
