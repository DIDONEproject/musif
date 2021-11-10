from typing import List

from musif.config import Configuration
from musif.extract.features.core.handler import DATA_KEY, DATA_MODE, DATA_TONALITY
from musif.musicxml.key import get_key_signature, get_key_signature_type

KEY = "Key"
KEY_SIGNATURE = "KeySignature"
KEY_SIGNATURE_TYPE = "KeySignatureType"
MODE = "Mode"

KEY_SIGNATURE_VALUES = ['b', 's']
MODE_VALUES = ['major', 'minor']


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):
    key = score_data[DATA_KEY]
    tonality = score_data[DATA_TONALITY]
    mode = score_data[DATA_MODE]
    key_signature = get_key_signature(key)
    key_signature_type = get_key_signature_type(key_signature)

    score_features.update({
        KEY: tonality,
        KEY_SIGNATURE: key_signature,
        KEY_SIGNATURE_TYPE: key_signature_type,
        MODE: mode,
    })


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    pass
