from typing import List, Optional, Tuple, Union

import pandas as pd
import roman
from music21 import pitch, scale
from music21.note import Note
from pandas.core.frame import DataFrame

import musif.extract.constants as C
from musif.extract.features.core.handler import DATA_KEY
from musif.extract.features.scale.constants import ACCIDENTAL_ABBREVIATION
from musif.logs import perr
from musif.musicxml.tempo import get_number_of_beats


def get_emphasised_scale_degrees_relative(
    notes_list: List[Note], score_data: dict, expanded: bool = False
) -> Optional[dict]:
    """Count one part's notes per scale degree relative to the local key.

    Returns None when the score carries no harmonic analysis, and an empty
    dict (after logging an error) when the degrees could not be computed.
    Pass ``expanded=True`` under ``expand_repeats``.
    """
    harmonic_analysis, tonality = extract_harmony(score_data)
    if harmonic_analysis.size == 0:
        return None
    try:
        keys_by_measure = _get_keys_by_measure(harmonic_analysis, tonality, expanded)
        emph_degrees = get_emphasized_degrees(notes_list, keys_by_measure)
    except Exception as e:
        file_name = score_data.get("file", "")
        perr(f"Could not compute relative degrees on {file_name}: {e!r}")
        emph_degrees = {}
    return emph_degrees


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
