from typing import Any, Optional


# TODO: do we really need a class containing a list of dictionaries? wouldn't a list of tuples be enough?
# consider this comment only if it is computationally critical, it is a well written class actually
class Cache:

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
