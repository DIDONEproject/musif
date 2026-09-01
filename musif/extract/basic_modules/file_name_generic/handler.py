from ntpath import basename
from typing import List

from musif.config import ExtractConfiguration
from musif.extract.constants import DATA_FILE
from musif.logs import lwarn
from .constants import *


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    """
    get variables from file_name
    returns a dictionary so it can be easily input in a df
    """

    file_name = basename(score_data[DATA_FILE])
    stem = file_name.rsplit(".", 1)[0] if "." in file_name else file_name
    artist, separator, title = stem.partition("_")
    if not separator:
        # no underscore: the whole stem is the title
        artist = ""
        title = stem

    score_features.update(
        {
            ARTIST: artist,
            TITLE: title,
        }
    )

def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    pass
