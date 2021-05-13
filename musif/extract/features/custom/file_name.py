from ntpath import basename
from typing import List

from musif.config import Configuration


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    """
    get variables from file_name
    returns a dictionary so it can be easily input in a df
    """

    file_name = basename(score_data["file"])

    opera_title = file_name[0:3]
    label = file_name.split("-", 2)[0]
    aria_id = file_name.split("[")[-1].split("]")[0]
    aria_title = file_name.split("-", 2)[1]
    year = file_name.split("-", -2)[-2]
    decade = str(int(year) // 100) + str(int(year[-2:]) // 10) + "0s"
    act = file_name.split("[", 1)[-1].split(".", 1)[0]
    scene = file_name.split(".", 1)[-1].split("]", 1)[0]

    return {
        "AriaOpera": opera_title,
        "AriaLabel": label,
        "AriaId": aria_id,
        "AriaName": aria_title,
        "Year": year,
        "Decade": decade,
        "Act": act,
        "Scene": scene,
        "ActAndScene": act + scene,
    }


def get_corpus_features(scores_data: List[dict], parts_data: List[dict], cfg: Configuration, scores_features: List[dict], corpus_features: dict) -> dict:
    return {}
