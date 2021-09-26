import copy
from typing import List, Tuple, Union

from music21.interval import Interval
from music21.key import Key
from music21.note import Note
from music21.scale import MajorScale, MinorScale
from music21.stream import Measure, Part, Score, Voice
from music21.text import assembleLyrics
from roman import toRoman

from musif.common import group


def get_key(score: Score) -> str:
    return str(score.analyze("key"))


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


def get_key_signature_type(key_signature: str) -> str:
    """
    returns the key signature type ('bb) for flats, 'ss' for sharps, and 'nn' for naturals
    """
    return key_signature[0]


def get_mode(key: str) -> str:
    if key.isupper():
        return 'M'
    else:
        return 'm'
