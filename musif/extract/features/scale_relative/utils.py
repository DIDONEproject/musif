from fractions import Fraction
from typing import List, Optional, Tuple, Union

import pandas as pd
import roman
from music21 import pitch, scale
from music21.note import Note
from music21.stream import Measure
from pandas.core.frame import DataFrame

import musif.extract.constants as C
from musif.extract.features.core.handler import DATA_KEY
from musif.extract.features.scale.constants import ACCIDENTAL_ABBREVIATION
from musif.logs import perr
from musif.musicxml.tempo import get_number_of_beats


def get_emphasised_scale_degrees_relative(
    notes_list: List[Note],
    score_data: dict,
    expanded: bool = False,
    positions: Optional[List[Tuple[int, float]]] = None,
) -> Optional[dict]:
    """Count one part's notes per scale degree relative to the local key.

    Returns None when the score carries no harmonic analysis, and an empty
    dict (after logging an error) when the degrees could not be computed.
    Pass ``expanded=True`` when the score was unfolded (``expand_repeats``).

    With ``positions`` (for each note, the 0-based position of its measure in
    the part and its onset in quarter notes within that measure, as given by
    the core module), each note takes the local key in force at its
    measure's position in the file and at its exact onset: the MuseScore
    file is the MusicXML file annotated bar for bar, so the n-th measure of
    the part is the analysis' ``mc`` n+1 (``playthrough`` n+1 when the score
    and the analysis were unfolded). Printed numbers cannot be trusted
    for this: Finale's "X1" bars carry, in music21, the number of the bar
    before them, which ms3 numbers differently (a final da capo bar was read
    in the key that closes the B section), and ms3 gives a second ending the
    number of the first. Where the two files are not barred alike, the
    printed numbers are used, as before.
    """
    harmonic_analysis, tonality = extract_harmony(score_data)
    if harmonic_analysis.size == 0:
        return None
    try:
        # an unfolded score was matched with its analysis, bar for bar, when
        # it was unfolded
        if positions is not None and (
            expanded or analysis_follows_measures(score_data)
        ):
            keys_by_position = _get_keys_by_position(harmonic_analysis, tonality)
            emph_degrees = _get_degrees_by_position(
                notes_list, positions, keys_by_position
            )
        else:
            keys_by_measure = _get_keys_by_measure(
                harmonic_analysis, tonality, expanded
            )
            emph_degrees = get_emphasized_degrees(notes_list, keys_by_measure)
    except Exception as e:
        file_name = score_data.get("file", "")
        perr(f"Could not compute relative degrees on {file_name}: {e!r}")
        emph_degrees = {}
    return emph_degrees


_FOLLOWS_MEASURES = "_analysis_follows_measures"


def analysis_follows_measures(score_data: dict) -> bool:
    """Whether the n-th measure of the score is the analysis' ``mc`` n+1, as
    when the MuseScore file is the MusicXML file annotated. Decided once per
    score (and per window) and kept in ``score_data``.

    The two are matched by length: every annotated measure is as long as the
    score's measure in that position (the longest of the parts, since a
    measure in which half of a split staff has nothing to play is empty).
    Failing that, by printed number: every annotated measure has the number
    the analysis gives it, Finale's "X" bars apart."""
    harmonic_analysis = score_data.get(C.DATA_MUSESCORE_SCORE)
    cached = score_data.get(_FOLLOWS_MEASURES)
    if cached is not None and cached[0] is harmonic_analysis:
        return cached[1]
    result = False
    score = score_data.get(C.DATA_SCORE)
    if (
        harmonic_analysis is not None
        and score is not None
        and _position_column(harmonic_analysis) is not None
    ):
        parts = [list(part.getElementsByClass(Measure)) for part in score.parts]
        result = _same_lengths(harmonic_analysis, parts) or _same_numbers(
            harmonic_analysis, parts[0] if parts else []
        )
    score_data[_FOLLOWS_MEASURES] = (harmonic_analysis, result)
    return result


def _position_column(harmonic_analysis: DataFrame) -> Optional[str]:
    """The column giving each label's measure position (1-based):
    ``playthrough``, which is ``mc`` in a folded analysis and the position in
    the unfolded sequence in an unfolded one; ``mc`` in a bare ms3 table."""
    for column in (C.PLAYTHROUGH, "mc"):
        if column in harmonic_analysis.columns:
            return column
    return None


def _same_lengths(harmonic_analysis: DataFrame, parts: List[list]) -> bool:
    if C.MEASURE_ACTUAL_DURATION not in harmonic_analysis.columns or not parts:
        return False
    number_of_measures = max(len(measures) for measures in parts)
    lengths = [
        max(
            Fraction(measures[index].duration.quarterLength).limit_denominator(10_000)
            for measures in parts
            if index < len(measures)
        )
        for index in range(number_of_measures)
    ]
    for position, act_dur in zip(
        harmonic_analysis[_position_column(harmonic_analysis)],
        harmonic_analysis[C.MEASURE_ACTUAL_DURATION],
    ):
        if pd.isna(position):
            continue
        position = int(position)
        if not 1 <= position <= number_of_measures or pd.isna(act_dur):
            return False
        if Fraction(str(act_dur)) * 4 != lengths[position - 1]:
            return False
    return True


def _same_numbers(harmonic_analysis: DataFrame, measures: list) -> bool:
    for position, mn in zip(
        harmonic_analysis[_position_column(harmonic_analysis)], harmonic_analysis["mn"]
    ):
        if pd.isna(position) or pd.isna(mn):
            continue
        position = int(position)
        if not 1 <= position <= len(measures):
            return False
        measure = measures[position - 1]
        if not measure.numberSuffix and measure.number != int(mn):
            return False
    return True


def _onset_in_quarters(value) -> Fraction:
    """An onset as an exact fraction of a quarter note (music21 gives floats
    and Fractions; floats are dyadic here, so the conversion is exact)."""
    return Fraction(value).limit_denominator(1_000_000)


def _get_keys_by_position(harmonic_analysis: DataFrame, tonality: str) -> dict:
    """Map every measure position between the first and the last annotated one
    (0-based: ``playthrough`` - 1) to the local key in force at its start and the
    (onset in quarter notes, key) changes inside it. ms3's ``mc_onset`` is
    counted, like music21's offsets, from the start of the measure as written
    (a pickup or a split bar starts at 0), in whole notes."""
    changes_by_position = {}
    key_cache = {}
    for position, mc_onset, localkey in zip(
        harmonic_analysis[_position_column(harmonic_analysis)],
        harmonic_analysis.mc_onset,
        harmonic_analysis.localkey,
    ):
        label = str(localkey).strip()
        if label in ("", "nan", "None", "@none") or pd.isna(position):
            continue
        if label not in key_cache:
            key_cache[label] = get_localTonalty(tonality, label)
        onset = Fraction(str(mc_onset)) * 4
        changes_by_position.setdefault(int(position) - 1, []).append(
            (onset, key_cache[label])
        )
    if not changes_by_position:
        raise ValueError("harmonic analysis contains no usable local keys")

    keys_by_position = {}
    current_key = None
    for position in range(min(changes_by_position), max(changes_by_position) + 1):
        changes = sorted(changes_by_position.get(position, []), key=lambda c: c[0])
        if current_key is None and changes:
            current_key = changes[0][1]
        keys_by_position[position] = (current_key, changes)
        if changes:
            current_key = changes[-1][1]
    return keys_by_position


def _get_degrees_by_position(
    notes_list: List[Note], positions: List[Tuple[int, float]], keys_by_position: dict
) -> dict:
    """Tally scale degrees, each note in the local key in force at its
    measure's position and onset. Before the first annotation a note takes
    the first key; after the last annotated measure, the last key."""
    notes_per_degree_relative = {
        to_full_degree(degree, accidental): 0
        for accidental in ["", "sharp", "flat"]
        for degree in [1, 2, 3, 4, 5, 6, 7]
    }
    first = min(keys_by_position)
    last = max(keys_by_position)
    first_key = keys_by_position[first][0]
    last_key, last_changes = keys_by_position[last]
    if last_changes:
        last_key = last_changes[-1][1]
    for note, (position, note_onset) in zip(notes_list, positions):
        if position < first:
            local_tonality = first_key
        elif position > last:
            local_tonality = last_key
        else:
            local_tonality, changes = keys_by_position[position]
            onset = _onset_in_quarters(note_onset)
            for change_onset, key in changes:
                if onset >= change_onset:
                    local_tonality = key
                else:
                    break
        if local_tonality is None:
            continue
        degree_value = get_note_degree(local_tonality, note.name)
        if degree_value is None:
            continue
        notes_per_degree_relative[degree_value] = (
            notes_per_degree_relative.get(degree_value, 0) + 1
        )
    return notes_per_degree_relative


def _get_keys_by_measure(
    harmonic_analysis: DataFrame, tonality: str, expanded: bool = False
) -> dict:
    """Map every measure (numbered as music21 numbers the notes) to the local
    key in force at its start, plus the (beat, key) changes inside it.

    Folded scores are keyed by the written measure number ``mn`` (for pickup
    scores ``playthrough`` is mn+1, which used to shift every key one bar);
    unfolded scores (``expand_repeats``) are keyed by ``playthrough``-1,
    matching music21's renumbering of the expanded score.
    """
    changes_by_measure = {}
    key_cache = {}
    for playthrough, mn, mc_onset, timesig, localkey in zip(
        harmonic_analysis[C.PLAYTHROUGH],
        harmonic_analysis.mn,
        harmonic_analysis.mc_onset,
        harmonic_analysis.timesig,
        harmonic_analysis.localkey,
    ):
        label = str(localkey).strip()
        if label in ("", "nan", "None", "@none"):
            continue
        measure = int(playthrough) - 1 if expanded else int(mn)
        if label not in key_cache:
            key_cache[label] = get_localTonalty(tonality, label)
        beat = _beat_in_measure(str(timesig), mc_onset)
        changes_by_measure.setdefault(measure, []).append(
            (beat, key_cache[label])
        )
    if not changes_by_measure:
        raise ValueError("harmonic analysis contains no usable local keys")

    keys_by_measure = {}
    current_key = None
    for measure in range(min(changes_by_measure), max(changes_by_measure) + 1):
        changes = sorted(changes_by_measure.get(measure, []), key=lambda c: c[0])
        if current_key is None and changes:
            current_key = changes[0][1]
        keys_by_measure[measure] = (current_key, changes)
        if changes:
            current_key = changes[-1][1]
    return keys_by_measure


def _beat_in_measure(timesig: str, mc_onset) -> float:
    """Convert an ms3 mc_onset (a fraction of a whole note from the measure
    start) into a 1-based beat position inside that measure."""
    beats = get_number_of_beats(timesig)
    if "/" in timesig:
        num, den = timesig.split("/")[:2]
        measure_whole_notes = int(num) / int(den)
    else:
        measure_whole_notes = 1.0
    if measure_whole_notes == 0:
        return 1.0
    return 1 + float(mc_onset) / measure_whole_notes * beats


def get_emphasized_degrees(notes_list: List[Note], keys_by_measure: dict) -> dict:
    """Resolve each note's local key from its measure (and the annotated
    changes inside that measure) and tally scale degrees."""
    notes_per_degree_relative = {
        to_full_degree(degree, accidental): 0
        for accidental in ["", "sharp", "flat"]
        for degree in [1, 2, 3, 4, 5, 6, 7]
    }
    first_measure = min(keys_by_measure)
    last_measure = max(keys_by_measure)
    for note in notes_list:
        measure = note.measureNumber
        if measure is None:
            continue
        measure = min(max(int(measure), first_measure), last_measure)
        local_tonality, changes = keys_by_measure[measure]
        try:
            beat = float(note.beat)
        except Exception:
            beat = None
        if beat is not None and beat == beat:  # NaN-safe
            for change_beat, key in changes:
                if beat >= change_beat:
                    local_tonality = key
                else:
                    break
        if local_tonality is None:
            continue
        degree_value = get_note_degree(local_tonality, note.name)
        if degree_value is None:
            continue
        if degree_value not in notes_per_degree_relative:
            notes_per_degree_relative[degree_value] = 1
        else:
            notes_per_degree_relative[degree_value] += 1
    return notes_per_degree_relative


def extract_harmony(score_data):
    harmonic_analysis = score_data.get(C.DATA_MUSESCORE_SCORE, pd.DataFrame())

    tonality = str(score_data[DATA_KEY])

    return harmonic_analysis, tonality


def get_note_degree(key: str, note: str) -> Optional[str]:
    """Scale degree of a note name relative to a key given as e.g. 'F#' /
    'e-' (uppercase tonic = major, lowercase = minor; the reference scale in
    minor is the natural minor, i.e. the key signature)."""
    if key[0].isupper():
        scl = scale.MajorScale(key.split(" ")[0])
    else:
        scl = scale.MinorScale(key.split(" ")[0])

    degree, accidental = scl.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch(note))
    accidental_name = accidental.fullName if accidental is not None else ""
    abbreviation = ACCIDENTAL_ABBREVIATION.get(accidental_name)
    if abbreviation is None:
        perr(f"Unsupported accidental {accidental_name!r} on note {note}; not counted")
        return None
    return abbreviation + str(degree)


def get_localTonalty(globalkey: str, degree: str) -> str:
    """Tonic of the local key expressed by a DCML degree label (a roman
    numeral with optional leading accidentals, possibly nested like 'V/V')
    relative to ``globalkey`` ('D major' / 'b minor' style).

    Returned uppercase for a major local key, lowercase for minor.
    """
    key_name = globalkey.split(" ")[0]
    is_major = "major" in globalkey
    for part in reversed(str(degree).split("/")):
        key_name, is_major = _tonic_from_degree(key_name, is_major, part)
    return key_name.upper() if is_major else key_name.lower()


def _tonic_from_degree(key_name: str, is_major: bool, degree: str) -> Tuple[str, bool]:
    sharps = degree.count("#")
    flats = degree.count("b")
    numeral = degree.replace("#", "").replace("b", "")
    degree_int = roman.fromRoman(numeral.upper())
    scl = scale.MajorScale(key_name) if is_major else scale.MinorScale(key_name)
    tonic = scl.pitchFromDegree(degree_int)
    for _ in range(sharps):
        tonic = tonic.transpose("A1")
    for _ in range(flats):
        tonic = tonic.transpose("-A1")
    return tonic.name, numeral.isupper()


def to_full_degree(degree: Union[int, str], accidental: str) -> str:
    return f"{ACCIDENTAL_ABBREVIATION[accidental]}{degree}"
