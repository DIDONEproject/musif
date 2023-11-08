import itertools
import re
from collections import Counter
from typing import Dict, List
from types import NoneType

import numpy as np
import pandas as pd
from ms3.expand_dcml import features2type, split_labels
from musif.logs import perr, pwarn
from urllib.request import urlopen
from musif.musicxml.tempo import get_number_of_beats
from musif.logs import perr, pwarn
from .constants import *

REGEX = {}


def get_harmonic_rhythm(ms3_table) -> dict:
    hr = {}
    measures = ms3_table.mn.dropna().tolist()
    measures_compressed = [i for j, i in enumerate(measures) if i != measures[j - 1]]
    numerals = ms3_table.numeral.dropna().tolist()
    number_of_chords = sum(Counter(numerals).values())
    time_signatures = ms3_table.timesig.tolist()
    harmonic_rhythm = (
        number_of_chords / len(measures_compressed)
        if len(measures_compressed) != 0
        else 0.0
    )

    if len(Counter(time_signatures)) == 1:
        harmonic_rhythm_beats = (
            number_of_chords
            / (get_number_of_beats(time_signatures[0]) * len(measures_compressed))
            if len(measures_compressed) != 0
            else 0.0
        )
    else:
        playthrough = ms3_table.playthrough.dropna().tolist()
        periods_ts = []
        time_changes = []

        for t in range(1, len(time_signatures)):
            if time_signatures[t] != time_signatures[t - 1]:

                # what measure in compressed list corresponds to the change in time signature
                time_changes.append(time_signatures[t - 1])
                periods_ts.append(
                    len(measures_compressed[0 : playthrough[t - 1]]) - sum(periods_ts)
                )
        harmonic_rhythm_beats = number_of_chords / sum(
            [
                period * get_number_of_beats(time_changes[j])
                for j, period in enumerate(periods_ts)
            ]
        ) if periods_ts else 0

    hr[HARMONIC_RHYTHM] = harmonic_rhythm
    hr[HARMONIC_RHYTHM_BEATS] = harmonic_rhythm_beats

    return hr


def get_measures_per_key(keys_options, measures, keys, mc_onsets, time_signatures):
    key_measures = {p: 0 for p in keys_options}
    last_key = 0
    done = 0
    starting_measure = 0

    new_measures = create_measures_extended(measures)
    numberofmeasures = len(new_measures)

    for i, key in enumerate(keys):
        if key != last_key and i < numberofmeasures:
            n_beats = int(get_number_of_beats(time_signatures[i - 1]))

            if last_key in key_measures:
                num_measures, done = compute_number_of_measures(
                    done,
                    starting_measure,
                    new_measures[i - 1],
                    new_measures[i],
                    mc_onsets[i],
                    n_beats,
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
        mc_onsets[numberofmeasures - 1],
        n_beats,
    )

    key_measures[last_key] += num_measures

    try:
        assert not (
            new_measures[0] == 0
            and round(sum(list(key_measures.values()))) != new_measures[i] + 1
        )
    except AssertionError as e:
        perr("There was an error counting the measures!: ", e)
        return {}
    return key_measures


def create_measures_extended(measures):
    new_measures = []
    new_measures.append(measures[0])
    for i in range(1, len(measures)):
        if measures[i] < max(measures[:i]):
            if same_measure(measures, i):
                new_measures.append(new_measures[i - 1])
            else:
                new_measures.append(new_measures[i - 1] + 1)
        else:
            new_measures.append(measures[i])
    return new_measures


def same_measure(measures, i):
    return measures[i] == measures[i - 1]


def compute_number_of_measures(
    done, starting_measure, previous_measure, measure, current_onset, num_beats
):
    starting_measure += done
    if measure == previous_measure:  # We are in the same measure, inside of it

        measures = previous_measure - 1 - starting_measure
        beat = current_onset.numerator
        # habrá que sumarle current_beat / max_beats. Antes convertir current_beat en numérico
        if type(current_onset) == str:
            numbers = current_onset.split(".")
            first = int(numbers[0])
            second = numbers[1].split("/")
            second = int(second[0]) / int(second[1])
            beat = first + second

        return (
            measures + beat / current_onset.denominator,
            beat / current_onset.denominator,
        )
        # before
        # return measures + beat/num_beats, beat/num_beats

    else:
        if (
            measure - previous_measure > 1
        ):  # Change of key happens in a change of measures
            return (
                previous_measure - starting_measure + (measure - 1 - previous_measure),
                0,
            )  ###WTF IS DIS
        else:
            return previous_measure - starting_measure, 0


#########################################################################
# Como sections tiene una indicación por compás, pero a lo largo del script
# trabajamos con la tabla harmonic_analysis, que tiene tantas entradas por
# compás como anotaciones harmónicas, repetimos las secciones según el número


def continued_sections(sections, mc):
    extended_sections = []
    repeated_measures = Counter(mc)
    for i, c in enumerate(repeated_measures):
        extended_sections.append([sections[i]] * repeated_measures[c])

    # Flat list
    return list(itertools.chain(*extended_sections))


################################################################################
# Function to return the harmonic function1 based on the global key mode. Uppercase if
# mode is major, lowercase if minor. 2nd, 4th, adn 6th degrees are considered
# as classes of subdominant function. In major mode, vi is treatred as the relative key (rm);
# in the minor, III = relative major (rj).
# Lowered degrees are indicated with 'b', raised with '#' (bII = Neapolitan key).
# Leading notes are abrreviated as LN.


def get_keys(list_keys, mode):
    result_dict = {t: get_function_first(t, mode) for t in set(list_keys)}
    # result_dict = {t: get_localkey_1(t, mode) for t in set(list_keys)}
    function1 = [result_dict[t] for t in list_keys]
    function2 = [get_function_second(g1) for g1 in function1]
    # function2 = [get_localkey_2(g1) for g1 in function1]
    return function1, function2


###################
# KEYAREAS
###################


def get_keyareas_lists(keys, g1, g2):
    key_areas = []
    key_areas_g1 = []
    key_areas_g2 = []
    last_key = ""
    for i, k in enumerate(keys):
        if k != last_key:
            key_areas.append(k)
            key_areas_g1.append(g1[i])
            key_areas_g2.append(g2[i])
            last_key = k
    return key_areas, key_areas_g1, key_areas_g2


def get_keyareas(lausanne_table, major=True):
    keys = lausanne_table.localkey.dropna().tolist()
    g1, g2 = get_keys(keys, "M" if major else "m")

    key_areas, key_areas_g1, key_areas_g2 = get_keyareas_lists(keys, g1, g2)
    number_blocks_keys = Counter(key_areas)
    # number_blocks_grouping1 = Counter(key_areas_g1)
    # number_blocks_grouping2 = Counter(key_areas_g2)
    measures = lausanne_table.mc.dropna().tolist()
    beats = lausanne_table.mc_onset.dropna().tolist()
    time_signatures = lausanne_table.timesig.tolist()

    key_measures = get_measures_per_key(
        list(set(keys)), measures, keys, beats, time_signatures
    )

    total_measures = float(sum(list(key_measures.values())))
    key_measures_percentage = {
        kc: float(key_measures[kc] / total_measures) for kc in key_measures
    }

    keyGrouping1_measures = get_measures_per_key(
        list(set(g1)), measures, g1, beats, time_signatures
    )
    keyGrouping1_measures = {
        kc: keyGrouping1_measures[kc] / sum(list(keyGrouping1_measures.values()))
        for kc in keyGrouping1_measures
    }
    keyGrouping2_measures = get_measures_per_key(
        list(set(g2)), measures, g2, beats, time_signatures
    )
    keyGrouping2_measures = {
        kc: keyGrouping2_measures[kc] / sum(list(keyGrouping2_measures.values()))
        for kc in keyGrouping2_measures
    }

    total_key_areas = sum(number_blocks_keys.values())
    # total_g1_areas = sum(number_blocks_grouping1.values())
    # total_g2_areas = sum(number_blocks_grouping2.values())

    # keyareas = {'TotalNumberKeyAreas': total_key_areas, 'TotalNumberMeasures': int(total_measures) }
    keyareas = {}
    for key in number_blocks_keys:
        keyareas[KEY_PREFIX + key + KEY_PERCENTAGE] = float(
            key_measures_percentage[key]
        )  # procentaje de compases de cada I, i, etc. en el total
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

    elif element.lower() in ["#vii", "vii"]:
        return "D"

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
    numerals = lausanne_table.numeral.dropna().tolist()
    keys = lausanne_table.globalkey.dropna().tolist()
    relativeroots = lausanne_table.relativeroot.tolist()

    _, ng2 = get_numerals_lists(
        numerals, relativeroots, keys
    )  # por que se coge solo la funcion segunda?? anyway cojamos los numerals
    numerals_counter = Counter(numerals)

    total_numerals = sum(list(numerals_counter.values()))
    nc = {}
    for n in numerals_counter:
        if str(n) == "":
            raise Exception("Some chords here are not parsed well")
            continue
        nc[NUMERALS_prefix + str(n) + "_Per"] = round(
            (numerals_counter[n] / total_numerals), 3
        )
        nc[NUMERALS_prefix + str(n) + "_Count"] = round((numerals_counter[n]), 3)

    return nc


def get_first_numeral(numeral, relativeroot, local_key):
    if str(relativeroot) != "nan":
        return get_function_first(numeral, "M" if relativeroot.isupper() else "m")
    else:
        return get_function_first(numeral, "M" if local_key.isupper() else "m")


def get_numerals_lists(list_numerals, list_relativeroots, list_local_keys):
    tuples = list(zip(list_numerals, list_relativeroots, list_local_keys))
    result_dict = {t: get_first_numeral(*t) for t in set(tuples)}
    function1 = [result_dict[t] for t in tuples if t]
    function2 = [get_function_second(g1) for g1 in function1 if type(g1) is not NoneType]
    return function1, function2


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

    chords_forms = make_type_col(
        lausanne_table
    )  # Nan values represent {} notations, not chords

    grouped_forms = get_chord_types_groupings(chords_forms)

    form_counter = Counter(grouped_forms)
    features_chords = {}
    for f in form_counter:
        features_chords[CHORD_TYPES_prefix + str(f)] = form_counter[f] / sum(
            list(form_counter.values())
        )
    return features_chords


def get_chords(harmonic_analysis):

    relativeroots = harmonic_analysis.relativeroot.tolist()
    keys = harmonic_analysis.localkey.dropna().tolist()
    chords = harmonic_analysis.chord.dropna().tolist()
    numerals = harmonic_analysis.numeral.dropna().tolist()
    types = [str(i) for i in harmonic_analysis.chord_type.dropna().tolist()]

    chords_functionalities1, chords_functionalities2 = get_chords_functions(
        chords, relativeroots, keys
    )

    numerals_and_types = [
        str(chord) + str(types[index]).replace("Mm", "").replace("mm", "")
        if types[index] not in ("M", "m") else str(chord) for index, chord in enumerate(numerals)]

    # chords_order = sort_labels(numerals_and_types, numeral=['I', 'i', 'V', 'v', 'VII', 'vii', 'II', 'ii', 'IV', 'iv','VI','vi','III','iii'], chordtype=['', '7', '+', 'o', '%', 'M', 'm','It'], drop_duplicates=True)
    chords_dict = count_chords(numerals_and_types)  # ,order)

    # Exception for #viio chords
    if "Chord_#viio" in chords_dict:
        chords_dict["Chord_viio"] = (
            chords_dict["Chord_viio"] + chords_dict.pop("Chord_#viio")
            if "Chord_viio" in chords_dict
            else chords_dict.pop("Chord_#viio")
        )

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
        return "mayor triad"
    elif chord_type in ["7", "mm7", "Mm7", "MM7", "mM7"]:
        return "7th"
    elif chord_type in ["o", "o7", "%", "%7"]:
        return "dim"
    elif chord_type in ["+", "+M7", "+m7"]:
        return "aug"
    else:
    #raise Exception:
        pwarn(f"Chord type {chord_type} not observed")
        return "other"


def get_chord_types_groupings(chordtype_list):
    return [get_chord_type(chord_type) for chord_type in chordtype_list]


def get_first_chord_local(chord, local_key):
    local_key_mode = "M" if local_key.isupper() else "m"

    if "/" not in chord:
        return get_function_first(parse_chord(chord), local_key_mode)
    else:
        parts = chord.split("/")
        degree = get_function_first(
            parse_chord(parts[0]), "M" if parts[1].isupper() else "m"
        )
        if len(parts) == 2:
            # relative = get_function_first(parts[1], local_key_mode)
            # return '/'.join([degree, relative])
            return degree

        else:
            relative_list = []
            relative_list.append(degree)
            relative_list.append(
                get_function_first(parts[1], "M" if parts[2].isupper() else "m")
            )
            for i in range(2, len(parts)):
                relative_list.append(get_function_first(parts[i], local_key_mode))
            # return '/'.join(relative_list)
            return degree


# Function to return second grouping for any chord in any given local key,
def get_second_grouping_localkey(first_grouping: str, relativeroot: str, local_key: str):
    mode = "M" if local_key else "m"
    if str(relativeroot) != "nan":
        mode = "M" if relativeroot.isupper() else "m"
    parts = first_grouping.split("/")

    degree = get_function_second(parts[0])
    if len(parts) == 2:
        chords = get_function_second(parts[1])  # , mode)
        return degree
        # return '/'.join([degree, chords])

    elif len(parts) == 3:
        # chord_1 = get_degree_2(parts[1], )
        relative_1 = get_function_second(
            parts[1]
        )  # , 'M' if parts[2].isupper() else 'm')
        relative_2 = get_function_second(parts[2])  # , mode)
        return "/".join([degree, relative_1, relative_2])
    return degree


def get_chords_functions(chords: List[str], relativeroots: List[str], local_keys: List[str]) -> list:

    chords_localkeys = list(zip(chords, local_keys))
    functionalities_dict = {t: get_first_chord_local(*t) for t in set(chords_localkeys)}

    first_function = [functionalities_dict[t] for t in chords_localkeys]
    first_function = [chord for chord in first_function if type(chord) != NoneType]
    
    # Redefine chords_localkeys to get second chord's functionality
    second_chords_localkeys = list(zip(first_function, relativeroots, local_keys))
    second_function = [
        get_second_grouping_localkey(*first_grouping)
        for first_grouping in second_chords_localkeys]

    return first_function, second_function


def make_type_col(df, num_col="numeral", form_col="form", fig_col="figbass"):
    param_tuples = list(
        df[[num_col, form_col, fig_col]].itertuples(index=False, name=None)
    )
    result_dict = {t: features2type(*t) for t in set(param_tuples)}
    return pd.Series(
        [result_dict[t] for t in param_tuples], index=df.index, name="chordtype"
    ).dropna()


def sort_labels(
    labels, git_branch="master", drop_duplicates=True, verbose=True, **kwargs
):
    """Sort a list of DCML labels following custom criteria.
        Uses: split_labels()
    Parameters
    ----------
    labels : :obj:`collection` or :obj:`pandas.Series`
        The labels you want to sort.
    git_branch : :obj:`str`, optional
        The branch of the DCMLab/standards repo from which you want to use the regEx.
    drop_duplicates : :obj:`bool`, optional
        By default, the function returns an ordered list of unique labels. Set to
        False in order to keep duplicate labels. Note that where the ordered features
        are identical, labels appear in the order of their occurrence.
    verbose : .obj:`bool`, optional
        By default, values that are missing from custom orderings are printed out.
        Pass False to prevent that.
    kwargs : {'values', 'occurrences', 'rvalues', 'roccurrences'}, :obj:`dict`, :obj:`list` or callable
        Pass one argument for every feature that you want to sort in the order
        in which features should be used for sorting. The arguments will be mapped
        on the respective columns which should yield alpha-numeric values to be sorted.
        globalkey
        localkey
        pedal
        chord
        numeral
        form
        figbass
        changes
        relativeroot
        pedalend
        phraseend
        chordtype
    Examples
    --------
    .. highlight:: python
        # Sort numerals by occurrences (descending), the figbass by occurrences (ascending), and
        # the form column by the given order
        sort_labels(labels, numeral='occurrences', figbass='roccurrences', form=['', '+', 'o', '%', 'M'])
        # Sort numerals by custom ordering and each numeral by the (globally) most frequent chord types.
        sort_labels(labels, numeral=['I', 'V', 'IV'], chordtype='occurrences')
        # Sort relativeroots alphabetically and the numerals by a custom ordering which
        # is equivalent to ['V', 'vii', '#vii']
        sort_labels(labels, relativeroot='rvalues', numeral={'vii': 5, 'V': 0,  '#vii': 10})
        # Sort chord types by occurrences starting with the least frequent and sort their inversions
        # following the given custom order
        sort_labels(labels, chordtype='roccurrences', figbass=['2', '43', '65', '7'])
    """
    if len(kwargs) == 0:
        raise ValueError("Pass at least one keyword argument for sorting...")
    if not isinstance(labels, pd.Series):
        if isinstance(labels, pd.DataFrame):
            raise TypeError("Pass only one column of your DataFrame.")
        labels = pd.Series(labels)
    if drop_duplicates:
        labels = labels.drop_duplicates()
    features = split_labels(labels, git_branch)

    def make_keys(col, order):
        def make_order_dict(it):
            missing = [v for v in col.unique() if v not in it]
            if len(missing) > 0 and verbose:
                print(
                    f"The following values were missing in the custom ordering for column {col.name}:\n{missing}"
                )
            return {v: i for i, v in enumerate(list(it) + missing)}

        if order in ["values", "rvalues"]:
            keys = sorted(set(col)) if order == "values" else reversed(sorted(set(col)))
            order_dict = make_order_dict(keys)
        elif order in ["occurrences", "roccurrences"]:
            keys = (
                col.value_counts(dropna=False).index
                if order == "occurrences"
                else col.value_counts(dropna=False, ascending=True).index
            )
            order_dict = make_order_dict(keys)
        elif order.__class__ is not dict:
            try:
                order_dict = make_order_dict(order)
            except:
                # order is expected to be a callable:
                return np.vectorize(order)(col)
        else:
            order_dict = order

        return np.vectorize(order_dict.get)(col)

    if "chordtype" in kwargs:
        features["chordtype"] = make_type_col(features)
    key_cols = {
        col: make_keys(features[col], order)
        for col, order in kwargs.items()
        if col in features.columns
    }
    df = pd.DataFrame(key_cols, index=features.index)
    ordered_ix = df.sort_values(by=df.columns.to_list()).index
    return labels.loc[ordered_ix]


def split_labels(labels, git_branch="master", dropna=True):
    """Split DCML harmony labels into their respective features using the regEx
        from the indicated branch of the DCMLab/standards repository.
    Parameters
    ----------
    labels : :obj:`pandas.Series`
        Harmony labels to be split.
    git_branch : :obj:`str`, optional
        The branch of the DCMLab/standards repo from which you want to use the regEx.
    dropna : :obj:`bool`, optional
        Drop rows where the regEx didn't match.
    """
    global REGEX
    if git_branch not in REGEX:
        url = f"https://raw.githubusercontent.com/DCMLab/standards/{git_branch}/harmony.py"
        glo, loc = {}, {}
        exec(urlopen(url).read(), glo, loc)
        REGEX[git_branch] = re.compile(loc["regex"], re.VERBOSE)
    regex = REGEX[git_branch]
    cols = [
        "globalkey",
        "localkey",
        "pedal",
        "chord",
        "numeral",
        "form",
        "figbass",
        "changes",
        "relativeroot",
        "pedalend",
        "phraseend",
    ]
    res = labels.str.extract(regex, expand=True)[cols]
    if dropna:
        return res.dropna(how="all").fillna("")
    return res.fillna("")
