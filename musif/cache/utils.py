import builtins
import pickle
import weakref
from pathlib import PurePath, Path
from typing import Any, List, Optional, Tuple

import music21 as m21
import pandas as pd

from musif.cache.cache import MethodCache, ObjectReference, SmartModuleCache


class FileCacheIntoRAM:
    """
    This class simply stores a dictionary of key-value. In `musif`, it is used to cache
    the objects (values) coming from the parsing of files (whose names are the keys). It
    is never written to disk and only kept into RAM.
    """

    def __init__(self, capacity: int):
        self._capacity = capacity
        self._items = []

    def put(self, key: str, value: Any):
        if self.full:
            del self._items[0]
        self._items.append({"key": key, "value": value})

    def get(self, key: str) -> Optional[Any]:
        for item in self._items:
            if item["key"] == key:
                return item["value"]
        return None

    def clear(self) -> None:
        self._items.clear()

    @property
    def full(self) -> bool:
        return len(self._items) == self._capacity


def iscache(obj1):
    """
    Check if `obj1` is a `SmartModuleCache` or a `MethodCache` object
    """
    if type(obj1) in (MethodCache, SmartModuleCache):
        return True
    return False


def isinstance(obj1, cls):
    """
    Check if obj1 is instance of `cls`. This function grants that `SmartModuleCache`
    objects are checked against their reference objects.
    """
    if type(obj1) is SmartModuleCache:
        t = obj1.cache["_type"]
        return builtins.issubclass(t, cls)
    else:
        return builtins.isinstance(obj1, cls)


def hasattr(obj1, attr):
    """
    Check if `obj1` has `attr`. This function grants that `SmartModuleCache` objects are
    checked against their cache or reference objects.
    """
    if type(obj1) is SmartModuleCache:
        ref = obj1.cache["_reference"].reference
        if ref is not None:
            return builtins.hasattr(ref, attr)
        else:
            return attr in obj1.cache
    else:
        return builtins.hasattr(obj1, attr)


def wrap_module_objects(
    obj: Any,
    target_addresses: List[str] = ["music21"],
    resurrect_reference: Optional[Tuple] = None,
    parent: Optional[ObjectReference] = None,
    name: Tuple[str] = ("",),
    args: Tuple[Optional[Tuple]] = (None,),
):
    """
    Returns the object wrapped with `SmartModuleCache` class if it was defined
    in one of the `target_addresses`

    If `obj` is a list or a tuple, e new list/tuple this function works
    recursively on their objects.

    If the object is an instance of `weakref.ReferenceType`
    this function converts the object to a regular
    reference and then applies the wrapping.
    """
    if isinstance(obj, weakref.ReferenceType):
        __import__('ipdb').set_trace()
        return obj()

    __module = obj.__class__.__module__
    for module in target_addresses:
        if __module.startswith(module):
            return SmartModuleCache(
                reference=obj,
                target_addresses=target_addresses,
                resurrect_reference=resurrect_reference,
                parent=parent,
                name=name,
                args=args,
            )

    if isinstance(obj, (list, tuple)):
        ret = [
            wrap_module_objects(
                v,
                target_addresses,
                resurrect_reference,
                parent,
                (*name, "__getitem__"),
                (*args, (i,)),
            )
            for i, v in enumerate(obj)
        ]
        if isinstance(obj, list):
            return ret
        elif isinstance(obj, tuple):
            return tuple(ret)
    return obj


def store_score_df(score, fname):
    """
    Stores `score` into `fname` (a file-like object, a string or a Path object)
    using dataframes and returns the object saved.

    The returned object is a dictionary with keys the name of the parts and values
    dataframes with the following columns:

    * "Type": A string identifying the type of object. Possible values: ``"Note"``,
        ``"Rest"``, ``"Measure"``,  ``"Time Signature"``
    * "Name": A string with the name of the note in Common Western Notation or with
        the time signature string for time signatures; for measures and rests, the value
        ``"-"`` is used.
    * "Value": The midi pitch for notes, -1 for others
    * "Measure Onset": The beat position of the object in reference to the beginning
        of the measure, -1 for measures
    * "Part Onset": The onset position of the object in reference to the beginning
        of the part
    * "Duration": The duration of the object, -1 for time signatures
    * "Tie": If a tie is applied to the note, its type is there (one of ``"start"``,
        ``"continue"``, ``"stop"``), otherwise ``"-"`` is used
    """

    def append_note(alist, note, offset, type, pitch=None, name=None):
        onset = offset + note.offset
        dur = note.duration.quarterLength
        m_onset = note.offset
        if pitch is None:
            pitch = note.pitch.midi
        if name is None:
            name = note.nameWithOctave
        if note.tie is not None:
            tie = note.tie.type
        else:
            tie = "-"
        alist.append((type, name, pitch, m_onset, onset, dur, tie))

    score_dict = {}
    for part in score.parts:
        data_part = []
        for measure in part.getElementsByClass(m21.stream.base.Measure):
            offset = measure.offset
            data_part.append(("Measure", "-", -1, -1, offset,
                              measure.duration.quarterLength, "-"))
            ts = measure.timeSignature
            if ts is not None:
                data_part.append(
                    (
                        "Time Signature",
                        ts.ratioString,
                        -1,
                        ts.offset,
                        ts.offset + offset,
                        -1,
                        "-",
                    )
                )
            for note in measure.flat.notesAndRests:
                if isinstance(note, m21.note.Note):
                    append_note(data_part, note, offset, "Note")
                elif isinstance(note, m21.note.Rest):
                    append_note(data_part, note, offset, "Rest", name="-", pitch=-1)
                elif isinstance(note, m21.chord.Chord):
                    for note in note.notes:
                        append_note(data_part, note, offset, "Note")
                else:
                    raise Exception(
                        f"Cannot handle this type of note: {note.cache['_type']}"
                    )
        data_part = pd.DataFrame(
            data_part,
            columns=(
                "Type",
                "Name",
                "Value",
                "Measure Onset",
                "Part Onset",
                "Duration",
                "Tie",
            ),
        )
        score_dict[part.partName] = data_part
    if isinstance(fname, (PurePath, str)):
        fname = Path(fname)
        fname.parent.mkdir(exist_ok=True)
        fname = open(fname, "wb")
    pickle.dump(score_dict, fname)
    return score_dict


def load_score_df(fname):
    """
    Loads a score object saved with `store_score_df` from a string or Path pointing to
    the file or from a file-like object. Return a dictionary of dataframes
    """
    if isinstance(fname, (PurePath, str)):
        fname = Path(fname)
        fname = open(fname, "rb")
    return pickle.load(fname)
