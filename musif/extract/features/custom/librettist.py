from typing import List

from music21.text import TextBox

from musif.config import Configuration

LIBRETTIST = "Librettist"


def get_score_features(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict) -> dict:
    """
    get variables from file_name
    returns a dictionary so it can be easily input in a df
    """

    score = score_data["score"]
    librettist = None
    for textbox in score.getElementsByClass(TextBox):
        lines = textbox.content.split("\n")
        for line in lines:
            if "Text:" in line:
                librettist = _extract_name(line.split(":")[1])
    return {
        LIBRETTIST: librettist,
    }


def _extract_name(text: str) -> str:
    chars = [char for char in text if char.isalpha() or char == " "]
    name = "".join(chars).strip()
    return name