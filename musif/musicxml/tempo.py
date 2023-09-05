import re
import xml.etree.ElementTree as ET
from enum import Enum
from typing import Optional

import pandas as pd


class TempoGroup2(Enum):
    """
    Contains constants refering to grouped tempo on the second level that will be used by the tempo module.
    """

    NA = "NA"
    SLOW = "Slow"
    MODERATE = "Moderate"
    FAST = "Fast"


def get_time_signature_type(time_signature: str) -> str:
    """
    Given a time signature, it returns  the correspondent type.

    Parameters
    ----------
        time_signature: str
        Time signature in the form of string separated by '/' to obtain the time signature type.
    """
    if time_signature in [
        "1/2",
        "1/4",
        "1/8",
        "1/16",
        "2/2",
        "2/4",
        "2/8",
        "2/16",
        "4/4",
        "C",
        "4/2",
        "4/8",
        "4/16",
        "8/2",
        "8/4",
        "8/8",
        "8/16",
    ]:
        return "simple duple"

    elif time_signature in ["6/8", "3/8", "12/2", "12/4", "12/8", "12/16"]:
        return "compound duple"

    elif time_signature in ["3/2", "3/4", "3/16", "6/2", "6/4", "6/16"]:
        return "simple triple"

    elif time_signature in ["9/2", "9/4", "9/8", "9/16"]:
        return "compound triple"

    else:
        return "other"


def get_tempo_grouped_1(tempo: str) -> str:
    """
    Returns a 1st level of grouping for the tempo markings, removing secondary labels
    and diminutive endings.

    Parameters
    ----------
        tempo: str
        Tempo string in italian to be extract the group from.

    """
    tempo = re.sub("\\W+", " ", tempo)  # removes eventual special characters
    replacements = [
        (w, "")
        for w in [
            "molto",
            "poco",
            "un poco",
            "tanto",
            "un tanto",
            "assai",
            "meno",
            "più",
            "piuttosto",
        ]
    ]
    if not tempo:
        return "NA"

    for r in replacements:
        tempo = tempo.replace(*r)
    tempo = (
        tempo.replace("Con brio", "brio")
        .replace("con brio", "brio")
        .replace("Con spirito", "spiritoso")
        .replace("con spirito", "spiritoso")
    )
    base_important_words = [
        "adagio",
        "allegro",
        "andante",
        "andantino",
        "largo",
        "lento",
        "presto",
        "vivace",
        "minueto",
    ]
    # if the tempo marking ends in -ietto and or -issimo, it retuns the marking without that ending
    important_words = (
        base_important_words
        + [w[0:-1] + "etto" for w in base_important_words]
        + [w[0:-1] + "ietto" for w in base_important_words]
        + [w[0:-1] + "issimo" for w in base_important_words]
        + [w[0:-1] + "ssimo" for w in base_important_words]
        + [w[0:-1] + "hetto" for w in base_important_words]
    )

    last_words = ""
    for word in tempo.split(" "):
        if word.lower() in important_words and (
            "ma non" not in last_words
            or " ma " not in last_words
            or "Tempo di" in last_words
        ):
            return word.capitalize()
        last_words += " " + word

    ################ SECOND IMPORTANT WORDS ################
    relevant_words = [
        "amoroso",
        "affettuoso",
        "agitato",
        "arioso",
        "cantabile",
        "comodo",
        "brio",
        "spiritoso",
        "espressivo",
        "fiero",
        "giusto",
        "grave",
        "grazioso",
        "gustoso",
        "maestoso",
        "moderato",
        "risoluto",
        "sostenuto",
        "spiritoso",
        "tempo",
    ]
    words_contained = []
    for word in tempo.split(" "):
        if word.lower() in relevant_words:
            words_contained.append(word)
    ## FINAL DECISION (Two exceptions: tempo and con brio) ##
    if len(words_contained) == 1:
        if words_contained[0].lower() not in ["tempo", "brio"]:
            return words_contained[0].capitalize()
        elif words_contained[0].lower() == "tempo":
            return "A tempo"
        else:
            return "Con brio"
    elif len(words_contained) > 1:
        for w in words_contained:
            if w[0].isupper():
                if w.lower() != "tempo":
                    return w  # returns the capitalized term
                elif w.lower() == "tempo":
                    return "A tempo"
                else:
                    return "Con brio"
        if words_contained[0] != "tempo":
            return words_contained[0].capitalize()
        elif words_contained[0] == "tempo":
            return "A tempo"  # or the first one
        else:
            return "Con brio"

    return "NA"


def get_tempo_grouped_2(tempo_grouped_1: str) -> str:
    """
    Returns a 2nd level of grouping for the tempo markings.

    Parameters
    ----------
        tempo_grouped_1: str
        Tempo string got from get_tempo_grouped_1
    """
    if tempo_grouped_1 is None or tempo_grouped_1.lower() == TempoGroup2.NA.value:
        return TempoGroup2.NA.value
    possible_terminations = ["ino", "etto", "ietto", "ssimo", "issimo", "hetto"]
    slow_basis = [
        "Adagio",
        "Affettuoso",
        "Grave",
        "Sostenuto",
        "Largo",
        "Lento",
        "Sostenuto",
    ]
    slow = slow_basis + [w[:-1] + t for w in slow_basis for t in possible_terminations]
    moderate_basis = [
        "Andante",
        "Arioso",
        "Comodo",
        "Cantabile",
        "Comodo",
        "Espressivo",
        "Grazioso",
        "Gustoso",
        "Maestoso",
        "Minueto",
        "Moderato",
        "Marcía",
        "Amoroso",
    ]
    moderate = moderate_basis + [
        w[:-1] + t for w in moderate_basis for t in possible_terminations
    ]
    fast_basis = [
        "Agitato",
        "Allegro",
        "Con brio",
        "Spiritoso",
        "Fiero",
        "Presto",
        "Risoluto",
        "Vivace",
    ]
    fast = fast_basis + [w[:-1] + t for w in fast_basis for t in possible_terminations]

    if tempo_grouped_1 in ["A tempo", "Giusto"]:
        return TempoGroup2.NA.value
    elif tempo_grouped_1 in slow:
        return TempoGroup2.SLOW.value
    elif tempo_grouped_1 in moderate:
        return TempoGroup2.MODERATE.value
    elif tempo_grouped_1 in fast:
        return TempoGroup2.FAST.value


def get_number_of_beats(time_signature: str) -> int:
    """
    Returns the number of beats corresponding to a time signature.

    By default, this returns the numerator, with the exceptions when the numerator is
    6, 9, or 12 and when the time signature is C or 3/8. If it is empty, it returns 1.
    If it is `"NA"`, it returns `pd.NA`.

    Parameters
    ----------
        time_signature: str
            Time signature in the form of string separated by '/' to obtain the time
            signature type.

    """
    # we only take the first time signature in case we receive more than one
    time_signature = time_signature.split(",")[0]
    if time_signature == "C":
        return 4
    elif time_signature == "":
        return 1
    elif time_signature == "NA":
        return pd.NA
    num, den = time_signature.split("/")
    if num == "3" and den == "8":
        return 1
    elif num == "6":
        return 2
    elif num == "9":
        return 3
    elif num == "12":
        return 4
    else:
        return int(num)
        # raise ValueError(f"The {time_signature} is not a known time signature")


def extract_numeric_tempo(file_path: str) -> Optional[int]:
    """
    Finds the numeric tempo in a musixml file by looking at the tempo marking in
    the xml code.

    Parameters
    ----------
        file_path: str
        Path to xml file to get the tempo from.

    """
    try:
        tree = ET.parse(file_path)
    except ET.ParseError as e:
        return "NA"

    root = tree.getroot()
    try:
        tempo = int(
            root.find("part")
            .find("measure")
            .find("direction")
            .find("sound")
            .get("tempo")
        )
    except:
        tempo = "NA"
    return tempo