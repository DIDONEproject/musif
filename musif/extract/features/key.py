from typing import List, Tuple

from music21.key import Key
from music21.stream import Score

from musif.config import Configuration

KEY = "Key"
KEY_SIGNATURE = "KeySignature"
KEY_SIGNATURE_GROUPED = "KeySignatureGrouped"
MODE = "Mode"


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    key = score_data["key"]
    tonality = score_data["tonality"]
    mode = score_data["mode"]
    key_signature = get_key_signature(key)
    key_signature_grouped = get_key_signature_grouped(key_signature)

    return {
        KEY: tonality,
        KEY_SIGNATURE: key_signature,
        KEY_SIGNATURE_GROUPED: key_signature_grouped,
        MODE: mode,
    }


def get_corpus_features(scores_data: List[dict], parts_data: List[dict], cfg: Configuration, scores_features: List[dict], corpus_features: dict) -> dict:
    return {}


def get_key_and_mode(score: Score) -> Tuple[Key, str, str]:
    """
    returns abbreviated designation of keys (uppercase for major mode; lowercase for minor mode)
    example: if key == 'D- major': return 'Db'
    """
    score_key = score.analyze("key")
    key_parts = score_key.name.split(" ")
    mode = key_parts[1].strip().lower()
    tonality = key_parts[0]
    tonality = tonality.lower() if mode == 'minor' else tonality.capitalize()
    tonality = tonality.replace('-', 'b')  # if the character '-' is not in the string, nothing will change
    return score_key, tonality, mode


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


