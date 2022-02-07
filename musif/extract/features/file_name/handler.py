from ntpath import basename
from typing import List

from musif.config import Configuration
from musif.extract.constants import DATA_FILE
from musif.logs import lwarn
from .constants import *


def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):
    """
    get variables from file_name
    returns a dictionary so it can be easily input in a df
    """

    file_name = basename(score_data[DATA_FILE])

    aria_id_end_idx = file_name.rfind("]")
    aria_id_start_idx = file_name.rfind("[", 0, aria_id_end_idx - 1) + 1
    aria_id = file_name[aria_id_start_idx: aria_id_end_idx]

    act_scene_end_idx = aria_id_start_idx - 2
    act_scene_start_idx = file_name.rfind("[", 0, act_scene_end_idx - 1) + 1
    act_and_scene = file_name[act_scene_start_idx: act_scene_end_idx]
    try:
        act, scene = act_and_scene.split(".")
    except ValueError:
        lwarn('Act and scene were not parsed well!')
        act = act_and_scene
        scene = ""
    composer_end_idx = act_scene_start_idx - 1
    composer_start_idx = file_name.rfind("-", 0, composer_end_idx - 1) + 1
    # composer = file_name[composer_start_idx: composer_end_idx]

    year_end_idx = composer_start_idx - 1
    year_start_idx = file_name.rfind("-", 0, year_end_idx - 1) + 1
    year= file_name[year_start_idx: year_end_idx]
    try:
        year = int(file_name[year_start_idx: year_end_idx])
    except ValueError:
        year = str(year)
    decade = str(year // 10) + "0s" if isinstance(year, int) else "nd"

    title_end_idx = year_start_idx - 1
    title_start_idx = file_name.rfind("-", 0, title_end_idx - 1) + 1
    aria_title = file_name[title_start_idx: title_end_idx]

    aria_labels = file_name[: title_start_idx - 1]
    opera_prefix = aria_labels[: 3]

    score_features.update({
        ARIA_OPERA: opera_prefix,
        ARIA_LABEL: aria_labels,
        ARIA_ID: aria_id,
        ARIA_NAME: aria_title,
        ARIA_YEAR: year,
        ARIA_DECADE: decade,
        ARIA_ACT: act,
        ARIA_SCENE: scene,
        ARIA_ACT_AND_SCENE: act + scene,
    })


def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    pass
