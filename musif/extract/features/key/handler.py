from typing import List

from musif.config import ExtractConfiguration
from musif.extract.features.core.handler import DATA_KEY, DATA_MODE, DATA_KEY_NAME
from musif.musicxml.key import (
    _get_key_signature,
    get_key_signature_type,
    get_name_from_key,
)
from .constants import *


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    key = score_data[DATA_KEY]
    key_name = score_data[DATA_KEY_NAME]
    mode = score_data[DATA_MODE]
    key_signature = _get_key_signature(key)
    key_signature = score_data[KEY_SIGNATURE]
    key_signature_type = get_key_signature_type(key_signature)

    score_features.update(
        {
            KEY: key_name,
            KEY_SIGNATURE: key_signature,
            KEY_SIGNATURE_TYPE: key_signature_type,
            MODE: mode,
        }
    )


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    pass
