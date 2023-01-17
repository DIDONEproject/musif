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
    name = file_name.split('.')[:-1]
    if '_' in name:
        name = name.split('_')
        title = name[0]
        artist = ""
    else:
        title = "".join(name)
        artist = ""
    artist = name[0]
    title = name[1]
        
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
