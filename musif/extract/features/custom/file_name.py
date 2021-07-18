from ntpath import basename
from typing import List

from musif.config import Configuration

ARIA_OPERA = "AriaOpera"
ARIA_LABEL = "AriaLabel"
ARIA_ID = "AriaId"
ARIA_NAME = "AriaName"
ARIA_YEAR = "Year"
ARIA_DECADE = "Decade"
ARIA_ACT = "Act"
ARIA_SCENE = "Scene"
ARIA_ACT_AND_SCENE = "ActAndScene"


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    """
    get variables from file_name
    returns a dictionary so it can be easily input in a df
    """

    file_name = basename(score_data["file"])

    aria_id_end_idx = file_name.rfind("]")
    aria_id_start_idx = file_name.rfind("[", 0, aria_id_end_idx - 1) + 1
    aria_id = file_name[aria_id_start_idx: aria_id_end_idx]

    act_scene_end_idx = aria_id_start_idx - 2
    act_scene_start_idx = file_name.rfind("[", 0, act_scene_end_idx - 1) + 1
    act_and_scene = file_name[act_scene_start_idx: act_scene_end_idx]
    act, scene = act_and_scene.split(".")

    composer_end_idx = act_scene_start_idx - 1
    composer_start_idx = file_name.rfind("-", 0, composer_end_idx - 1) + 1
    composer = file_name[composer_start_idx: composer_end_idx]

    year_end_idx = composer_start_idx - 1
    year_start_idx = file_name.rfind("-", 0, year_end_idx - 1) + 1
    year = int(file_name[year_start_idx: year_end_idx])
    decade = str(year // 10) + "0s"

    title_end_idx = year_start_idx - 1
    title_start_idx = file_name.rfind("-", 0, title_end_idx - 1) + 1
    aria_title = file_name[title_start_idx: title_end_idx]

    aria_labels = file_name[: title_start_idx - 1]
    opera_prefix = aria_labels[: 3]

    return {
        ARIA_OPERA: opera_prefix,
        ARIA_LABEL: aria_labels,
        ARIA_ID: aria_id,
        ARIA_NAME: aria_title,
        ARIA_YEAR: year,
        ARIA_DECADE: decade,
        ARIA_ACT: act,
        ARIA_SCENE: scene,
        ARIA_ACT_AND_SCENE: act + scene,
    }


