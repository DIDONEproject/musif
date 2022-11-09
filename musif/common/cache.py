import random
from typing import Any, Dict, List, Optional, Tuple, Union

from musif.logs import pinfo

from .exceptions import CannotResurrectObject


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

    After unpickling, the referenced object is no longer available.
    If `resurrect_reference` is not None, it will be loaded using its value. In
    such a case, `resurrect_reference` should be a tuple with a function in the
    first position and the arguments later; the function returned value must be
    the reference object.

    If the method/property/field returns an object defined in a
    one of the `target_addresses`, this class will return a wrapped version of
    that object.
    In `musiF`, this is used to wrap all the music21 objects and to cache
    (most of) music21 operations.

    When a method is called, it is matched with all the arguments, similarly to
    `functools.lru_cache`, thus using the hash value of the objects.

    When pickled, this objects only pickles the cache dictionary.
    The matching of the arguments in a method works on a custom hash value that
    is guaranteed to be the same when the object is pickled/unpickled. As
    consequence, as long as the method arguments are `SmartModuleCache`
    objects, they will re-use the cache after pickling/unpickling.
    This will automatically work for objects in the `target_module`.

    N.B. However, if one method is called with as argument an object that is
    not a singleton and not in `target_module`, the call will be cached but
    after pickling it cannot be used, thus leading to an always increasing
    cach.

    NotImplemented: When `smart_pickling` is True, it pickles the dictionary
    alone, without the reference, otherwise, it pickles the reference as well.
    """

    def __init__(
        self,
        reference: Any = None,
        target_addresses: List[str] = ["music21"],
        resurrect_reference: Optional[Tuple] = None,
    ):

        self.cache: Dict[
            str,
            Union[Tuple, str, int, SmartModuleCache, MethodCache, Any],
        ] = {
            "_hash": random.randint(10**10),
            "_target_addresses": target_addresses,
            "_repr": str(reference),
            "_reference": ObjectReference(reference, resurrect_reference),
        }

    def __repr__(self):
        _repr = self.cache["_repr"]
        _module = self.cache["_target_module"]
        _resurrect = self.cache["_resurrect_reference"]
        return f"SmartModuleCache({_resurrect}, {_module}, {_repr})"

    @property
    def target_addresses(self):
        return self.cache["_target_addresses"]

    @target_addresses.setter
    def target_addresses(self, value):
        self.cache["_target_addresses"] = value

    def __hash__(self):
        return self.cache["_hash"]

    def __getattribute__(self, name: str) -> Any:
        """
        The real key of this class is this method!
        """
        attr = self.cache.get(name)
        if attr is not None:
            # attr is in cache
            return attr
        else:
            # attr not in cache
            return self._cache_new_attr(name)

    def _cache_new_attr(self, name: str) -> Any:
        attr = self.cache["_reference"].get_attr(name)
        if callable(attr):
            # pass the method cacher
            self.cache[name] = MethodCache(self.cache["_reference"])
        else:
            # cache the value and returns it
            self.cache[name] = wrap_module_objects(
                attr, target_addresses=self.cache["_target_addresses"]
            )
        return attr

    def __setstate__(self, state):
        self.cache = state

    def __getstate__(self):
        return self.cache


class ObjectReference:
    """
    This is handles the calls to the reference object so that both
    `MethodCache` and `SmartModuleCache` reference the same object and when one
    resurrects it, the other sees it.
    """

    def __init__(self, reference: Any, resurrect_reference: Optional[Tuple]):
        self.reference = reference
        self.resurrect_reference = resurrect_reference

    def _try_resurrect(self) -> None:
        if self._resurrect_reference is None:
            raise CannotResurrectObject(self)
        else:
            func = self._resurrect_reference[0]
            args = self._resurrect_reference[1:]
            self.reference = func(*args)

    def get_attr(self, name: str) -> Any:
        if self.reference is None:
            pinfo(f"Resurrecting reference object due to call to attribute {name}")
            self._try_resurrect()
        return getattr(self.reference, name)

    def __getstate__(self):
        return self.resurrect_reference

    def __setstate__(self, state):
        self.reference = None
        self.resurrect_reference = state


class CallableArguments:
    """
    This class represents a set of ordered arguments.
    The hash is the concatenation of the argument hashes.
    If the arguments persists the hash across pickling, this object persists
    the hash as well.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        h = ""
        for i in range(len(self.args)):
            h += str(hash(self.args[i]))

        for i in self.kwargs:
            h += str(hash(self.kwargs[i]))
        self._hash = int(h)

    def __hash__(self):
        return self._hash


class MethodCache:
    """
    A simple wrapper that checks if the arguments are in the
    cache, otherwise runs the method and caches the arguments
    """

    def __init__(
        self,
        reference: ObjectReference,
        attr_name: str,
        target_addresses: List[str] = ["music21"],
    ):
        self.reference = reference
        self.attr_name = attr_name
        self.attr_cache = dict()
        self.target_addresses = target_addresses

    def __call__(self, *args, **kwargs):
        call_args = CallableArguments(*args, **kwargs)
        cached_res = self.attr_cache.get(call_args)
        if cached_res is not None:
            return cached_res
        else:
            attr = self.reference.get_attr(self.attr_name)
            res = attr(*args, **kwargs)
            res = wrap_module_objects(res, target_addresses=self.target_addresses)
            self.attr_cache[call_args] = res
            return res


def wrap_module_objects(
    obj: Any,
    target_addresses: List[str] = ["music21"],
    resurrect_reference: Optional[Tuple] = None,
):
    """
    Returns the object wrapped with `SmartModuleCache` class if it was defined
    in one of the `target_addresses`
    """
    __module = obj.__class__.__module__
    for module in target_addresses:
        if __module.startswith(module):
            return SmartModuleCache(
                reference=obj,
                target_addresses=target_addresses,
                resurrect_reference=resurrect_reference,
            )
    return obj
