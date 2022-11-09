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
