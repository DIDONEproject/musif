import builtins
import pickle
from pathlib import PurePath
from typing import Any, List, Optional, Tuple

import music21 as m21
import pandas as pd

from musif.cache.cache import MethodCache, ObjectReference, SmartModuleCache


class FileCacheIntoRAM:
    """
    This class simply stores a dictionary of key-value.
    In `musiF`, it is used to cache the objects (values) coming from the
    parsing of files (whose names are the keys).
    It is never written to disk and only kept into RAM.
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
    """
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
        else:
            return tuple(ret)

    return obj


def load_scores(fname):
    """
    Open `fname` (a file-like object, a string or a Path object)
    and returns a dataframe with most of the information in it
    """
    # from music21.note import Note

    if isinstance(fname, (PurePath, str)):
        fname = open(fname, "rb")
    cached_score = pickle.load(fname)["score"]

    def append_note(alist, note, offset, pitch=None, name=None):
        onset = offset + note.offset
        dur = note.duration.quarterLength
        if pitch is None:
            pitch = note.pitch.midi
        if name is None:
            name = note.nameWithOctave
        alist.append((name, pitch, onset, dur))

    score = {'timeSignatures': []}
    for part in cached_score.parts:
        ts = part.getTimeSignatures()
        score['timeSignatures'] += [t.ratioString for t in ts]
        data_part = []
        for measure in part.getElementsByClass(m21.stream.base.Measure):
            offset = measure.offset
            for note in measure.notesAndRests:
                if isinstance(note, m21.note.Note):
                    append_note(data_part, note, offset)
                elif isinstance(note, m21.note.Rest):
                    append_note(data_part, note, offset, name='rest', pitch=-1)
                elif isinstance(note, m21.chord.Chord):
                    for note in note.notes:
                        append_note(data_part, note, offset)
                else:
                    raise Exception(
                        f"Cannot handle this type of note: {note.cache['_type']}"
                    )
        data_part = pd.DataFrame(
            data_part, columns=("Name", "Pitch", "Onset", "Duration")
        )
        score[part.partName] = data_part
    __import__('ipdb').set_trace()
    return score


if __name__ == "__main__":
    load_scores(
        "/home/federico/musiF_tests/data/cache/Did05M-Fra_lo-1769-Majo[1.08][0293].pkl"
    )
