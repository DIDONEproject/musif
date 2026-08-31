import re
from collections import Counter
from typing import Dict, List

import pandas as pd
from musif.logs import pwarn
from musif.musicxml.tempo import get_number_of_beats
from .constants import *


def get_harmonic_rhythm(ms3_table, number_of_measures=None) -> dict:
    """Harmonic annotations per measure and per beat.

    The denominator covers ALL measures of the piece (or window): pass the
    real measure count as ``number_of_measures``; without it, the highest
    playthrough measure carrying a label is used as an approximation.
    """
    hr = {}
    numerals = [n for n in ms3_table.numeral.dropna().tolist() if str(n) != "@none"]
    number_of_chords = len(numerals)
    playthrough = ms3_table.playthrough.dropna().tolist()
    time_signatures = ms3_table.timesig.tolist()

    if number_of_measures is None or not number_of_measures == number_of_measures:
        number_of_measures = max(playthrough) if playthrough else 0
    number_of_measures = int(number_of_measures)

    harmonic_rhythm = (
        number_of_chords / number_of_measures if number_of_measures else 0.0
    )

    total_beats = _total_beats(playthrough, time_signatures, number_of_measures)
    harmonic_rhythm_beats = number_of_chords / total_beats if total_beats else 0.0

    hr[HARMONIC_RHYTHM] = harmonic_rhythm
    hr[HARMONIC_RHYTHM_BEATS] = harmonic_rhythm_beats

    return hr


def _total_beats(playthrough, time_signatures, number_of_measures) -> float:
    """Beats in measures 1..number_of_measures, forward-filling the metre
    from the labelled measures (every period counts, including the last)."""
    timesig_by_measure = {}
    for measure, timesig in zip(playthrough, time_signatures):
        timesig_by_measure.setdefault(int(measure), str(timesig))
    if not timesig_by_measure or number_of_measures <= 0:
        return 0.0
    current = timesig_by_measure[min(timesig_by_measure)]
    total = 0.0
    for measure in range(1, number_of_measures + 1):
        current = timesig_by_measure.get(measure, current)
        total += get_number_of_beats(current)
    return total


def get_measures_per_key(keys_options, measures, keys, mc_onsets, time_signatures):
    key_measures = {p: 0 for p in keys_options}
    last_key = 0
    done = 0
    starting_measure = 0

    new_measures = measures
    numberofmeasures = len(new_measures)

    for i, key in enumerate(keys):
        if key != last_key and i < numberofmeasures:
            if last_key in key_measures:
                num_measures, done = compute_number_of_measures(
                    done,
                    starting_measure,
                    new_measures[i - 1],
                    new_measures[i],
                    _measure_fraction(time_signatures[i], mc_onsets[i]),
                )
                key_measures[last_key] += num_measures

            last_key = key
            starting_measure = new_measures[i] - 1

    # last!
    num_measures, _ = compute_number_of_measures(
        done,
        starting_measure,
        new_measures[numberofmeasures - 1],
        new_measures[numberofmeasures - 1] + 1,
        _measure_fraction(
            time_signatures[numberofmeasures - 1], mc_onsets[numberofmeasures - 1]
        ),
    )

    key_measures[last_key] += num_measures

    return key_measures


def _measure_fraction(timesig, mc_onset) -> float:
    """Convert an ms3 mc_onset (a fraction of a whole note) into a fraction
    of its measure, using the measure length implied by the time signature."""
    timesig = str(timesig)
    if "/" in timesig:
        num, den = timesig.split("/")[:2]
        measure_whole_notes = int(num) / int(den)
    else:
        measure_whole_notes = 1.0
    return float(mc_onset) / measure_whole_notes if measure_whole_notes else 0.0


def compute_number_of_measures(
    done, starting_measure, previous_measure, measure, onset_fraction
):
    starting_measure += done
    if measure == previous_measure:  # the key changes inside this measure
        measures = previous_measure - 1 - starting_measure
        return measures + onset_fraction, onset_fraction

    # the key changes in a later measure: the old key owns everything up to
    # that measure plus the fractional onset of the change inside it
    whole_measures = previous_measure - starting_measure + (
        measure - 1 - previous_measure
    )
    return whole_measures + onset_fraction, onset_fraction


################################################################################
# Function to return the harmonic function1 based on the global key mode. Uppercase if
# mode is major, lowercase if minor. 2nd, 4th, adn 6th degrees are considered
# as classes of subdominant function. In major mode, vi is treatred as the relative key (rm);
# in the minor, III = relative major (rj).
# Lowered degrees are indicated with 'b', raised with '#' (bII = Neapolitan key).
# Leading notes are abrreviated as LN.


###################
# KEYAREAS
###################


def get_keyareas(lausanne_table):
    # row-aligned extraction: independent dropna() calls used to shift the
    # zip whenever one column had a gap
    rows = lausanne_table[["localkey", "playthrough", "mc_onset", "timesig"]]
    rows = rows.dropna(subset=["localkey", "playthrough"])
    keys = rows.localkey.tolist()

    key_areas = []
    last_key = ""
    for k in keys:
        if k != last_key:
            key_areas.append(k)
            last_key = k
    number_blocks_keys = Counter(key_areas)

    # playthrough is the exact per-playthrough measure counter (monotonic
    # even under expand_repeats, where mc jumps backwards)
    measures = [int(m) for m in rows.playthrough.tolist()]
    beats = [0 if b != b else b for b in rows.mc_onset.tolist()]
    time_signatures = rows.timesig.tolist()

    key_measures = get_measures_per_key(
        list(set(keys)), measures, keys, beats, time_signatures
    )

    total_measures = float(sum(list(key_measures.values())))
    key_measures_percentage = {
        kc: float(key_measures[kc] / total_measures) for kc in key_measures
    }

    total_key_areas = sum(number_blocks_keys.values())

    keyareas = {}
    for key in number_blocks_keys:
        keyareas[KEY_PREFIX + key + KEY_PERCENTAGE] = float(
            key_measures_percentage[key]
        )  # percentage of measures spent in each local key
        keyareas[KEY_PREFIX + KEY_MODULATORY + key] = (
            number_blocks_keys[key] / total_key_areas
        )

    return keyareas


def get_function_first(element, mode):
    reference = {
        "T": ["i"],
        "D": ["v", "vii"],
        "SD": ["ii", "iv", "vi"],
        "MED": ["iii"],
    }

    # Special chords
    if any([i for i in ("It", "Ger", "Fr") if i in element]):
        return "D"

    elif element.lower() == "bii":
        return "NAP"

    if mode == "M":
        if element == "vii":
            return "D"
        elif element == "#vii":
            return "#ln"
        elif element == "bVII":
            return "ST"
        elif element == "bvii":
            return "st"
        elif element == "VII":
            return "LN"

    if mode == "m":
        if element == "#vii":
            return "D"
        elif element == "VII":
            return "ST"
        elif element == "bVII":
            return "bST"
        elif element == "bvii":
            return "bst"
        elif element == "#VII":
            return "LN"
        elif element == "vii":
            return "st"

    element = element.replace("b", "-")  # '-' represents flats
    for key, value in reference.items():
        if element.replace("#", "").replace("-", "").lower() in value:
            output = key.lower() if element.islower() else key
            if "-" in element:
                output = "-" + output
            elif "#" in element:
                output = "#" + output
            return output.replace("-", "b")


def get_function_second(element):
    if element is None:
        return None
    element = element.replace("b", "-")
    if element.lower() == "#ln":
        return "#ST"
    elif element in ["rm", "rj"]:
        return "rel"
    elif element.upper() in ["ST", "LN"]:
        return "ST"
    else:
        return element.upper().replace("-", "b")


def get_numerals(lausanne_table):
    numerals = [
        n
        for n in lausanne_table.numeral.dropna().tolist()
        if str(n) not in ("", "@none")
    ]
    numerals_counter = Counter(numerals)

    total_numerals = sum(list(numerals_counter.values()))
    nc = {}
    for n in numerals_counter:
        nc[NUMERALS_prefix + str(n) + "_Per"] = numerals_counter[n] / total_numerals
        nc[NUMERALS_prefix + str(n) + "_Count"] = numerals_counter[n]

    return nc


def get_additions(lausanne_table):
    additions = lausanne_table.changes.tolist()
    total_chords = len(lausanne_table.chord.tolist())
    
    additions_cleaned = []
    for i, a in enumerate(additions):
        if isinstance(a, int):
            additions_cleaned.append(int(a))
        else:
            additions_cleaned.append(str(a))

    additions_counter = Counter(additions_cleaned)
    additions_dict = {
        ADDITIONS_4_6_64: 0,
        ADDITIONS_9: 0,
        OTHERS_NO_AUG: 0,
        OTHERS_AUG: 0,
    }
    for a in additions_counter:
        c = additions_counter[a]
        a = str(a)
        if a == "+9":
            additions_dict[ADDITIONS_9] = c
        elif a in ["4", "6", "64", "4.0", "6.0", "64.0"]:
            additions_dict[ADDITIONS_4_6_64] += c
        elif "+" in a:
            additions_dict[OTHERS_AUG] += c
        elif str(a) == "nan":
            continue
        else:
            additions_dict[OTHERS_NO_AUG] += c

    additions = {}
    for a in additions_dict.keys():
        if additions_dict[a] != 0:
            # additions[ADDITIONS_prefix + str(a)] = additions_dict[a] / sum(
                # list(additions_dict.values())
            additions[ADDITIONS_prefix + str(a)] = additions_dict[a] / total_chords
    return additions


def get_chord_types(lausanne_table):
    # ms3's chord_type column is assigned BEFORE special labels are expanded,
    # so it still says It/Ger/Fr for augmented sixths; re-deriving the type
    # from the post-expansion numeral (the old make_type_col) could never
    # produce them, leaving the documented aug6 bucket unreachable
    rows = lausanne_table[["numeral", "chord_type"]].dropna(subset=["chord_type"])
    rows = rows[rows.numeral.astype(str) != "@none"]
    chords_forms = [str(t) for t in rows.chord_type.tolist()]

    grouped_forms = get_chord_types_groupings(chords_forms)

    form_counter = Counter(grouped_forms)
    features_chords = {}
    for f in form_counter:
        features_chords[CHORD_TYPES_prefix + str(f)] = form_counter[f] / sum(
            list(form_counter.values())
        )
    return features_chords


def _strip_accidentals(label: str) -> str:
    return str(label).replace("#", "").replace("b", "")


def get_chords(harmonic_analysis):
    # row-aligned extraction: only rows that carry a chord label (phrase-only
    # rows have a propagated localkey but no chord, and used to shift the
    # pairing); '@none' rows are explicit non-harmony and are excluded
    rows = harmonic_analysis[["chord", "localkey", "numeral", "chord_type"]]
    rows = rows.dropna(subset=["chord"])
    rows = rows[rows.numeral.astype(str) != "@none"]

    keys = rows.localkey.tolist()
    chords = rows.chord.tolist()
    numerals = rows.numeral.tolist()
    types = [str(i) for i in rows.chord_type.tolist()]

    chords_functionalities1, chords_functionalities2 = get_chords_functions(
        chords, keys
    )

    numerals_and_types = []
    for index, numeral in enumerate(numerals):
        chord_type = types[index]
        if chord_type in ("It", "Ger", "Fr"):
            # augmented sixths keep their own label (ms3 rewrites their
            # numeral to vii/V, which used to produce 'viiIt'-style names)
            numerals_and_types.append(chord_type)
        elif chord_type in ("M", "m"):
            numerals_and_types.append(str(numeral))
        else:
            numerals_and_types.append(str(numeral) + _seventh_suffix(chord_type))

    # #viio chords are counted together with viio
    numerals_and_types = [
        "viio" + label[len("#viio"):] if label.startswith("#viio") else label
        for label in numerals_and_types
    ]

    chords_dict = count_chords(numerals_and_types)

    counter_function_1 = Counter(chords_functionalities1)
    counter_function_2 = Counter(chords_functionalities2)
    chords_group_1 = count_chords_group(counter_function_1, "1")
    chords_group_2 = count_chords_group(counter_function_2, "2")

    return chords_dict, chords_group_1, chords_group_2


def count_chords(chords: list, order: List[str] = []) -> Dict[str, str]:
    chords_numbers = Counter(chords)
    # chords_numbers=sort_dict(chords_numbers, order)

    total_chords = sum(chords_numbers.values())

    chords_dict = {}
    for degree in chords_numbers:
        chords_dict[CHORD_prefix + degree + "_Per"] = (
            chords_numbers[degree] / total_chords
        )
        chords_dict[CHORD_prefix + degree + "_Count"] = chords_numbers[degree]
    return chords_dict


def count_chords_group(counter_function: List[str], number: str) -> Dict[str, str]:
    chords_group = {}
    total_chords_group = sum(Counter(counter_function).values())

    for degree in counter_function:
        chords_group[CHORDS_GROUPING_prefix + number + degree + "_Per"] = (
            counter_function[degree] / total_chords_group
        )
        chords_group[
            CHORDS_GROUPING_prefix + number + degree + "_Count"
        ] = counter_function[degree]

    return chords_group


def _seventh_suffix(chord_type: str) -> str:
    """Collapse every major/minor seventh quality (Mm7, mm7, MM7, mM7) to a
    plain '7' suffix; o7/%7/+7 keep their symbols."""
    for prefix in ("MM", "mM", "Mm", "mm"):
        if chord_type.startswith(prefix):
            return chord_type[len(prefix):]
    return chord_type


def parse_chord(chord):
    if "(" in chord:
        chord = chord.split("(")[0]
    if "o" in chord:
        chord = chord.split("o")[0]
    if "+" in chord:
        chord = chord.split("+")[0]
    if "%" in chord:
        chord = chord.split("%")[0]
    if "M" in chord:
        chord = chord.split("M")[0]

    # return chord letter without number
    return re.split("(\d+)", chord)[0]


def get_chord_type(chord_type):
    chord_type = str(chord_type)
    if chord_type == "m":
        return "minor triad"
    elif chord_type == "M":
        return "major triad"
    elif chord_type in ["7", "mm7", "Mm7", "MM7", "mM7"]:
        return "7th"
    elif chord_type in ["o", "o7", "%", "%7"]:
        return "dim"
    elif chord_type in ["+", "+M7", "+m7", "+7"]:
        return "aug"
    elif chord_type in ["It", "Ger", "Fr"]:
        return "aug6"
    else:
        pwarn(f"Chord type {chord_type} not observed")
        return "other"


def get_chord_types_groupings(chordtype_list):
    return [get_chord_type(chord_type) for chord_type in chordtype_list]


def get_first_chord_local(chord, local_key):
    # DCML rule (ms3's series_is_minor): a key is minor only when the numeral
    # is all-lowercase - 'bVI' is a MAJOR local key despite isupper()==False
    local_key_mode = "m" if _strip_accidentals(local_key).islower() else "M"

    if "/" not in chord:
        return get_function_first(parse_chord(chord), local_key_mode)
    # applied chords (X/Y[/Z]): classify the chord against its direct reference
    parts = chord.split("/")
    return get_function_first(
        parse_chord(parts[0]),
        "m" if _strip_accidentals(parts[1]).islower() else "M",
    )


def get_chords_functions(chords: List[str], local_keys: List[str]) -> list:
    chords_localkeys = list(zip(chords, local_keys))
    functionalities_dict = {t: get_first_chord_local(*t) for t in set(chords_localkeys)}

    # unclassifiable chords are dropped from BOTH groupings together, keeping
    # every list aligned with its source row
    first_function = []
    second_function = []
    for chord, local_key in chords_localkeys:
        function = functionalities_dict[(chord, local_key)]
        if function is None:
            continue
        first_function.append(function)
        second_function.append(get_function_second(function))

    return first_function, second_function


