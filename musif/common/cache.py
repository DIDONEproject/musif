from typing import Any, Optional


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


class SmartModuleCache:
    """
    This class wraps any object so that its function calls can be cached in a
    dict, very similarly to how `functools.lru_cache` works.

    The object keeps a dictionary and a reference to the wrapped object.
    Each time a method, a field, or a property is called, it stores the result
    value in the dictionary.
    When the same call is performed a second time, the result value is taken
    from the dictionary.

    If the method/property/field returns an object defined in a
    `target_module`, this class will returned a wrapped version of that object.
    In `musiF`, this is used to wraps all the music21 objects and to cache
    (most of) all music21 operations.

    When a method is called, it is matched with all the arguments, as
    `functools.lru_cache` does, thus using the hash value of the objects.

    When pickled, this objects only pickles the cache dictionary.
    The matching of the arguments works on a custom hash value that is
    guaranteed to be the same when the object is pickled/unpickled. As
    consequence, as long as the method arguments are `SmartModuleCache`
    objects, they will re-use the cache after pickling/unpickling.
    This will automatically work for objects in the `target_module`.

    After unpickling, the referenced object is no longer available.
    If `resurrect_reference` is not None, it will be loaded using its value. In
    such a case, `resurrect_reference` should be a tuple with a function in the
    first position and the arguments later; the function returned value must be
    the reference object.

    NotImplemented: When `smart_pickling` is True, it pickles the dictionary
    alone, without the reference, otherwise, it pickles the reference as well.
    """
