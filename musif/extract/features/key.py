from typing import Tuple

from music21.key import Key
from music21.stream import Score


def get_global_features(score: Score) -> dict:
    score_key = score.analyze("key")
    key, mode = get_key_and_mode(score_key)
    key_signature = get_key_signature(score_key)
    key_signature_grouped = get_key_signature_grouped(key_signature)

    return {
        "Key": key,
        "KeySignature": key_signature,
        "KeySignatureGrouped": key_signature_grouped,
        "Mode": mode,
    }


def get_key(score: Score) -> str:
    score_key = score.analyze("key")
    return get_key_and_mode(score_key)[0]


def get_key_and_mode(score_key: Key) -> Tuple[str, str]:
    """
    returns abbreviated designation of keys (uppercase for major mode; lowercase for minor mode)
    example: if key == 'D- major': return 'Db'
    """
    key_parts = score_key.name.split(" ")
    mode = key_parts[1].strip().lower()
    tonality = key_parts[0]
    tonality = tonality.lower() if mode == 'minor' else tonality.capitalize()
    tonality = tonality.replace('-', 'b')  # if the character '-' is not in the string, nothing will change
    return tonality, mode


def get_key_signature(score_key: Key) -> str:
    if score_key.sharps:
        key_signature = "b" * abs(score_key.sharps) if score_key.sharps < 0 else "s" * score_key.sharps
    else:
        key_signature = "n"
    return key_signature


def get_key_signature_grouped(key_signature: str) -> str:
    """
    returns the key signature type ('bb) for flats, 'ss' for sharps, and 'nn' for naturals
    """
    return key_signature[0]


def get_mode(key: str) -> str:
    if key.isupper():
        return 'M'
    else:
        return 'm'


