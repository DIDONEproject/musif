import itertools
from typing import Union

import ms3
import music21 as m21
import pandas as pd
from music21.stream.base import Measure
from pandas import DataFrame

import musif.extract.constants as C
from musif.cache import isinstance
from musif.extract.constants import PLAYTHROUGH
from musif.logs import pwarn
from musif.musicxml.tempo import get_number_of_beats

file_names = []
repeat_bracket = False


def process_musescore_file(file_path: str, expand_repeats: bool = False) -> DataFrame:
    """
    Given a mscx file name, parses the file using ms3 library and returns a dataframe containing all harmonic information.
    Adds Playthrough column that contains number of every measure in the cronological order
    Parameters
    ----------
    file_path: str
        Path to mscx file
    expand_repeats: bool
        Directory path to musescore file
    Returns
    -------
    harmonic_analysis: str
        Dataframe containing harmonic information
    """

    msc3_score = ms3.score.Score(file_path, logger_cfg={"level": "ERROR"})
    harmonic_analysis = msc3_score.mscx.expanded()
    harmonic_analysis.reset_index(inplace=True)
    if expand_repeats:
        harmonic_analysis = msc3_score.mscx.expanded(unfold=True)
        harmonic_analysis.reset_index(inplace=True)
        # unfolded_mc=msc3_score.mscx.measures().set_index("mc").next
        # mn = next2sequence(unfolded_mc)
        # mn = ms3.utils.next2sequence(unfolded_mc)
        # mn = pd.Series(mn, name="mc_playthrough")
        # harmonic_analysis = ms3.utils.unfold_repeats(harmonic_analysis, mn)
        harmonic_analysis.rename(columns={"mc_playthrough": PLAYTHROUGH}, inplace=True)
    else:
        harmonic_analysis = msc3_score.mscx.expanded()
        harmonic_analysis.reset_index(inplace=True)
        if harmonic_analysis.mn[0] == 0:
            harmonic_analysis[PLAYTHROUGH] = harmonic_analysis["mc"]
        else:
            harmonic_analysis[PLAYTHROUGH] = harmonic_analysis["mn"]
    _include_beats_column(harmonic_analysis)
    return harmonic_analysis


def expand_score_repetitions(score, repeat_elements: list):
    """
    Given a music21 Score object and a list containing repetition elements, expands the score object and
    places all measures in their correspondent cronological order
    Parameters
    ----------
    score: music21 Score
        Score object parsed by music21
    expand_repeats: list
        List containing all repetition elements
    Returns
    -------
    final_score: music21 Score
        Score object with expanded repetitions
    """

    score = _expand_repeat_bars(score)
    final_score = m21.stream.Score()
    final_score.metadata = score.metadata

    if len(repeat_elements) > 0:
        for part in score.parts:
            p = _expand_part(part, repeat_elements)

            final_score.insert(0, p)
    else:
        final_score = score
    return final_score


def _measure_ranges(
    instrument_measures: int,
    init: int,
    end: int,
    iteration: int = None,
    offset: int = None,
    twocompasses_flag: bool = False,
    remove_repetition_marks_flag: bool = False,
) -> list:
    measures = []
    o = offset
    last_offset = (
        0.0 if int(init) - 6 < 0 else instrument_measures[int(init) - 6].offset
    )

    init_index, end_index = _find_init_and_end_indexes(instrument_measures, init, end)
    for i in range(init_index, end_index + 1):
        if (
            not i < 0
            and i < len(instrument_measures)
            and instrument_measures[i].measureNumber >= int(init)
            and instrument_measures[i].measureNumber <= int(end)
        ):
            if not twocompasses_flag:
                compass = instrument_measures[i].quarterLength
                m = m21.stream.Measure(number=instrument_measures[i].measureNumber)
                if remove_repetition_marks_flag:
                    m.elements = [
                        e
                        for e in instrument_measures[i].elements
                        if not isinstance(e, m21.repeat.RepeatMark)
                    ]
                else:
                    m.elements = instrument_measures[i].elements
                m.quarterLength = compass
                if offset is None:
                    m.offset = last_offset
                else:
                    m.offset = o
                    o += compass

                measures.append(m)
                if (
                    instrument_measures[i].measureNumber != 0.0
                    and instrument_measures[i].offset != 0
                ):
                    last_offset = instrument_measures[i].offset + compass
            twocompasses_flag = False

    if iteration == 2:
        last_measure = instrument_measures[i + 1]
        last_measure.offset = measures[-1].offset
        measures = measures[:-1] + [last_measure]
    return measures


def _find_init_and_end_indexes(
    instrument_measures: list, init: int, end: int
) -> Union[int, int]:
    init_index = instrument_measures.index(
        [m for m in instrument_measures if m.measureNumber == init][0]
    )
    end_compass = [m for m in instrument_measures if m.measureNumber == end]
    end_index = (
        instrument_measures.index(end_compass[0])
        if len(end_compass) > 0
        else len(instrument_measures) - 1
    )
    return init_index, end_index


def _get_instrument_elements(part):
    measures = []
    for elem in part:
        if isinstance(elem, m21.stream.Measure):
            measures.append(elem)
            # Change the note offsets to avoid problems due to the slurs
            last_offset = 0
            last_duration = 0
            for note in elem:
                if (
                    isinstance(note, m21.note.Note)
                    or isinstance(note, m21.note.Rest)
                    or isinstance(note, m21.chord.Chord)
                ):
                    note.offset = last_offset + last_duration
                    last_offset = note.offset
                    last_duration = note.duration.quarterLength
    return measures


def get_repetition_elements(score, v=True):
    global repeat_bracket
    repeat_bracket = False
    repeat_elements = set()

    for instruments in score.parts:
        instr_repeat_elements = []
        for elem in instruments.elements:
            if isinstance(elem, m21.stream.Measure):
                for e in elem:
                    if isinstance(e, m21.repeat.RepeatMark) and not isinstance(
                        e, m21.bar.Repeat
                    ):
                        measure = e.measureNumber
                        if elem.numberSuffix in ["X1", "X2"]:  # Exception
                            measure += 1
                        instr_repeat_elements.append((measure, e.name))
            elif isinstance(elem, m21.spanner.RepeatBracket):
                repeat_bracket = True
                string_e = str(elem)
                index = string_e.find("music21.stream.Measure")
                string_e = string_e[index:].replace("music21.stream.Measure ", "")
                measure = (
                    string_e.split(" ")[0].strip().replace("X1", "").replace("X2", "")
                )
                instr_repeat_elements.append(
                    (int(measure), "repeat bracket" + elem.number)
                )
        repeat_elements.update(instr_repeat_elements)

    repeat_elements = sorted(list(repeat_elements), key=lambda tup: tup[0])
    if v:
        print("The repeat elements found in this score are: " + str(repeat_elements))
    return repeat_elements


def _include_beats_column(harmonic_analysis: DataFrame) -> None:
    harmonic_analysis["beats"] = 0
    for index, measure in enumerate(harmonic_analysis[PLAYTHROUGH].values):
        if measure <= 1:
            beat = int(
                measure
                + float(harmonic_analysis.mc_onset[index])
                * get_number_of_beats(harmonic_analysis.timesig[index])
            )
        else:
            time_sig = get_number_of_beats(harmonic_analysis.timesig[index - 1])
            beat = int(
                (measure - 1) * time_sig
                + 1
                + harmonic_analysis.mc_onset[index]
                * get_number_of_beats(harmonic_analysis.timesig[index])
            )

        harmonic_analysis.at[index, "beats"] = beat


def _get_beat_position(
    beats_timesignature: int, number_of_beats: int, pos: int
) -> float:
    if number_of_beats == beats_timesignature:
        return pos
    else:
        return (pos / beats_timesignature) + 1


def _expand_repeat_bars(score):
    final_score = m21.stream.Score()
    final_score.metadata = score.metadata
    exist_repetition_bars = False

    # find repeat bars and expand
    for instr in score.parts:
        part_measures = _get_instrument_elements(
            instr.elements
        )  # returns the measures with repetitions
        last_measure = part_measures[-1].measureNumber
        part_measures_expanded = []
        startsin0 = part_measures[0].measureNumber == 0  # Everything should be -1
        repetition_bars = []

        # Find all repetitions in that instrument
        for elem in instr.elements:
            if isinstance(elem, m21.stream.Measure):
                exist_repetition_bars = _examine_measure(repetition_bars, elem)
            elif isinstance(elem, m21.spanner.RepeatBracket):
                _examine_repeat_bracket(instr, repetition_bars, elem)
        repetition_bars = sorted(list(repetition_bars), key=lambda tup: tup[0])

        start = 0 if startsin0 else 1
        _append_repetitions(
            final_score,
            exist_repetition_bars,
            instr,
            part_measures,
            last_measure,
            part_measures_expanded,
            repetition_bars,
            start,
        )

    return final_score if exist_repetition_bars else score


def _append_repetitions(
    final_score,
    exist_repetition_bars,
    instr,
    part_measures,
    last_measure,
    part_measures_expanded,
    repetition_bars,
    start,
):
    if exist_repetition_bars:
        p = m21.stream.Part()
        p.id = instr.id
        p.partName = instr.partName
        for repetition_bar in repetition_bars:
            measure = _measure_ranges(
                part_measures, repetition_bar[0], repetition_bar[0]
            )[0].quarterLength
            if repetition_bar[1] == "start":
                start = _add_start(
                    part_measures,
                    part_measures_expanded,
                    start,
                    repetition_bar,
                    measure,
                )
            elif repetition_bar[1] == "end":
                start = _add_end(
                    part_measures,
                    part_measures_expanded,
                    repetition_bars,
                    start,
                    repetition_bar,
                    measure,
                )
        if start < last_measure:
            measure = _measure_ranges(part_measures, start, start + 1)[0].quarterLength
            offset = part_measures_expanded[-1][-1].offset
            part_measures_expanded.append(
                _measure_ranges(
                    part_measures, start, last_measure + 1, offset=offset + measure
                )
            )

        p.elements = list(itertools.chain(*tuple(part_measures_expanded)))
        final_score.insert(0, p)


def _add_end(
    part_measures,
    part_measures_expanded,
    repetition_bars,
    start,
    repetition_bar,
    measure,
):
    if len(part_measures_expanded) > 0:
        offset = part_measures_expanded[-1][-1].offset
    else:
        offset = 0
    casilla_1 = (
        True
        if any(re[1] == "1" and re[0] <= repetition_bar[0] for re in repetition_bars)
        else False
    )
    casilla_2 = None
    if casilla_1:
        casilla_2 = [
            re for re in repetition_bars if re[1] == "2" and re[0] > repetition_bar[0]
        ]
        casilla_2 = None if len(casilla_2) == 0 else casilla_2[0]
    part_measures_expanded.append(
        _measure_ranges(
            part_measures,
            init=start,
            end=repetition_bar[0],
            offset=offset + measure,
            remove_repetition_marks_flag=True,
        )
    )  # This should erase the repetition marks
    if casilla_2 != None:
        part_measures_expanded.append(
            _measure_ranges(
                part_measures,
                start,
                casilla_2[0],
                iteration=2,
                offset=part_measures_expanded[-1][-1].offset + measure,
            )
        )
        start = casilla_2[0] + 1
    else:
        part_measures_expanded.append(
            _measure_ranges(
                part_measures,
                init=start,
                end=repetition_bar[0],
                offset=part_measures_expanded[-1][-1].offset + measure,
            )
        )
        start = repetition_bar[0] + 1
    return start


def _add_start(part_measures, part_measures_expanded, start, repetition_bar, measure):
    if len(part_measures_expanded) > 0:
        offset = part_measures_expanded[-1][-1].offset
    else:
        offset = 0
    start_measures = _measure_ranges(
        part_measures, start, repetition_bar[0] - 1, offset=offset + measure
    )
    if len(start_measures) > 0:
        part_measures_expanded.append(start_measures)
    start = repetition_bar[0]
    return start


def _examine_repeat_bracket(instr, repetition_bars, elem):
    string_e = str(elem)
    index = string_e.find("music21.stream.Measure")
    measure = string_e[index:].replace("music21.stream.Measure", "")[1:3].strip()
    repetition_bars.append((int(measure), elem.number))
    index = instr.elements.index(elem)
    elem.elements = instr.elements[:index] + instr.elements[index + 1 :]


def _examine_measure(repetition_bars, elem):
    for e in elem:
        if isinstance(e, m21.bar.Repeat):
            exist_repetition_bars = True
            if e.direction == "start":
                repetition_bars.append((e.measureNumber, "start"))
            elif e.direction == "end":
                repetition_bars.append((e.measureNumber, "end"))
            index = elem.elements.index(e)
            elem.elements = elem.elements[:index] + elem.elements[index + 1 :]
    return exist_repetition_bars


def _get_measures_list(part_measures: list, repeat_elements: list):
    measures_list = []
    startsin0 = part_measures[0].measureNumber == 0  # Everything should be -1

    there_is_fine = False
    there_is_segno = False
    # 1. find the fine and segno
    if any([r[1] == "fine" for r in repeat_elements]):
        f = [x[0] for x in repeat_elements if x[1] == "fine"][0]
        there_is_fine = True
    if any([r[1] == "segno" for r in repeat_elements]):
        s = [x[0] for x in repeat_elements if x[1] == "segno"][0]
        there_is_segno = True

    # Having all the repetition elements, get the measures
    if there_is_segno:
        before_segno = _measure_ranges(part_measures, 1 if not startsin0 else 0, s - 1)
        measures_list.append(
            before_segno
        )  # S -1 OR S-> when segno in compass 1, s, else s-1?
        dc_time_signature = [
            y
            for x in before_segno
            for y in x.elements
            if isinstance(y, m21.meter.TimeSignature)
        ]
    elif there_is_fine:
        measures_list.append(
            _measure_ranges(
                part_measures,
                1 if not startsin0 else 0,
                f - 1,
                iteration=1 if repeat_bracket else None,
            )
        )
    else:
        measures_list.append(
            _measure_ranges(
                part_measures,
                1 if not startsin0 else 0,
                len(part_measures),
                iteration=1 if repeat_bracket else None,
            )
        )

    for repeat in repeat_elements:
        repeat_measure = _measure_ranges(part_measures, repeat[0], repeat[0])
        compass = repeat_measure[0].quarterLength

        if repeat[1] == "segno":
            offset = measures_list[-1][-1].offset
            segno_part = _measure_ranges(
                part_measures,
                s,
                f - 1 if there_is_fine else len(part_measures),
                iteration=1 if repeat_bracket else None,
                offset=offset + compass,
                remove_repetition_marks_flag=True,
            )
            measures_list.append(segno_part)  # Segno to Fine
        elif repeat[1] == "fine":
            twoCompasses = False
            """if len(repeat_measure) > 0:
                twoCompasses = True"""
            offset = measures_list[-1][-1].offset
            fine_part = _measure_ranges(
                part_measures,
                f,
                len(part_measures),
                offset=offset + compass,
                twocompasses_flag=twoCompasses,
                remove_repetition_marks_flag=True,
            )
            measures_list.append(fine_part)  # Fine to end
        elif repeat[1] == "al segno" or repeat[1] == "dal segno":
            offset = measures_list[-1][-1].offset
            # segnos' compass time signature
            segno_time_measure = [
                x
                for x in segno_part[0].elements
                if isinstance(x, m21.meter.TimeSignature)
            ]
            segno_time_measure = (
                segno_time_measure
                if len(segno_time_measure) != 0
                else dc_time_signature[-1]
            )
            alsegno_list = _measure_ranges(
                part_measures,
                s,
                f - 1 if there_is_fine else len(part_measures),
                iteration=2 if repeat_bracket else None,
                offset=offset + compass,
                remove_repetition_marks_flag=True,
            )
            if not any(
                isinstance(x, m21.meter.TimeSignature) for x in alsegno_list[0].elements
            ):
                # we reset the time signature that was on the dacapo
                alsegno_list[0].elements = tuple(
                    [segno_time_measure] + list(alsegno_list[0].elements)
                )

            measures_list.append(alsegno_list)  # Segno to fine
        elif repeat[1] == "da capo":
            offset = measures_list[-1][-1].offset
            if startsin0 and there_is_fine and not repeat_bracket:
                f += 1
            dacapo_list = _measure_ranges(
                part_measures,
                0 if startsin0 else 1,
                f - 1 if there_is_fine else len(part_measures),
                iteration=2 if repeat_bracket else None,
                offset=offset + compass,
                remove_repetition_marks_flag=True,
            )
            measures_list.append(dacapo_list)

    return measures_list


def _expand_part(part, repeat_elements: list):
    part_measures = _get_instrument_elements(
        part.elements
    )  # returns the measures with repetitions
    p = m21.stream.Part()
    p.id = part.id
    p.partName = part.partName

    part_measures_expanded = _get_measures_list(
        part_measures, repeat_elements
    )  # returns the measures expanded
    part_measures_expanded = list(itertools.chain(*part_measures_expanded))
    # Assign a new continuous measure number to every measure
    measure_number = 0 if part_measures_expanded[0].measureNumber == 0 else 1
    for i, e in enumerate(part_measures_expanded):
        m = m21.stream.Measure(number=measure_number)
        m.elements = e.elements
        m.offset = e.offset
        m.quarterLength = e.quarterLength
        part_measures_expanded[i] = m
        measure_number += 1
    p.elements = part_measures_expanded
    return p


def _calculate_total_number_of_beats(time_signatures: list) -> int:
    """
    Given a list of time signatures, sums the beats of each time signature
    """
    # periods = _get_timesignature_periods(time_signatures)
    return sum(get_number_of_beats(ts) for ts in time_signatures)


def cast_mixed_dtypes(col):
    if "mixed" in pd.api.types.infer_dtype(col):
        notna = col.notna()
        newtype = col[notna].map(type).mode()[0]
        if issubclass(newtype, float):
            #  convert fractions like '1/3' to float
            col[notna] = col[notna].apply(pd.eval)
            col = col.convert_dtypes()
        elif issubclass(newtype, int):
            # convert to string
            col = col.astype("string")
    return col


def extract_global_time_signature(score_data):
    """
    Extracts a global time signature for the score for cases where is not possibel to get measure-by-measure TS
    """
    try:
        global_ts = (
            score_data[C.DATA_FILTERED_PARTS][0]
            .getElementsByClass(Measure)[0]
            .timeSignature
        )
    except IndexError:
        global_ts = None
        
    if global_ts is None:
        pwarn("Couldn't extract global time signature!")
        global_ts = "NA"
        
    score_data[C.GLOBAL_TIME_SIGNATURE] = global_ts
    return global_ts
