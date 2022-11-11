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


class SmartCache:
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

    Any object returned by accessing an attribute is cached with `SmartCache`

    When a method is called, it is matched with all the arguments, similarly to
    `functools.lru_cache`, thus using the hash value of the objects.

    When pickled, this objects only pickles the cache dictionary.
    The matching of the arguments in a method works on a custom hash value that
    is guaranteed to be the same when the object is pickled/unpickled. As
    consequence, as long as the method arguments are `SmartCache`
    objects, they will re-use the cache after pickling/unpickling.
    This will automatically work for objects in the `target_module`.

    Sometimes, the methods of the referenced object expect a non-cached module,
    for instance when a type checking or a hash comparison is done. For those
    situations, `SmartCache` provides *special methods* that start with
    `SmartCache.SPECIAL_METHODS_NAME` (which defaults to
    `"smartcache__"`). It is possible call any method with
    `smartcache__methoname`, e.g. `score.smartcache__remove`.
    When a special method is called, the first call is performed with the
    non-cached arguments, as it would happen without `SmartCache`.

    N.B. However, if one method is called with as argument an object that is
    not a singleton and not in `target_module`, the call will be cached but
    after pickling it cannot be used, thus leading to an always increasing
    cach.

    NotImplemented: When `smart_pickling` is True, it pickles the dictionary
    alone, without the reference, otherwise, it pickles the reference as well.
    """

    SPECIAL_METHODS_NAME = "smartcache__"

    def __init__(
        self,
        reference: Any = None,
        resurrect_reference: Optional[Tuple] = None,
    ):

        cache: Dict[str, Union[Tuple, str, int, SmartCache, MethodCache, Any],] = {
            "_hash": random.randint(10**10, 10**15),
            "_reference": ObjectReference(reference, resurrect_reference),
        }
        object.__setattr__(self, "cache", cache)

    def __repr__(self):
        _module = self.cache["_target_addresses"]
        _reference = self.cache["_reference"]
        return f"SmartCache({_reference}, {_module})"

    def __hash__(self):
        return self.cache["_hash"]

    def _wmo(self, obj):
        return wrap_module_objects(
            obj,
            resurrect_reference=None,
        )

    def __getattr__(self, name: str) -> Any:
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

    def __delattr__(self, name):
        del self.cache[name]

    def __setattr__(self, name, value):
        self.cache[name] = self._wmo(value)
        self.cache["_reference"].get_attr("__setattr__")(name, value)

    def _cache_new_attr(self, name: str) -> Any:
        if name.startswith(self.SPECIAL_METHODS_NAME):
            special_name = name
            name = name[len(self.SPECIAL_METHODS_NAME) :]
        else:
            special_name = None
        attr = self.cache["_reference"].get_attr(name)
        if callable(attr):
            # use the method cacher
            attr = MethodCache(
                self.cache["_reference"],
                name,
                special_method=special_name is not None,
            )
        else:
            # cache the value and returns it
            attr = self._wmo(attr)

        if special_name is not None:
            name = special_name
        self.cache[name] = attr
        return attr

    def __setstate__(self, state):
        object.__setattr__(self, "cache", state)

    def __getstate__(self):
        return self.cache

    # caching other special methods
    def __iter__(self):
        it = self.cache.get("__list__")
        if it is None:
            it = self.cache["_reference"].get_attr("__iter__")()
            it = list(map(self._wmo, it))
            self.cache["__list__"] = it
        return iter(it)

    def __len__(self):
        L = self.cache.get("__len__")
        if L is None:
            L = self.cache["_reference"].get_attr("__len__")()
            self.cache["__len__"] = L
        return L

    def __getitem__(self, k):
        v = self.cache.get(f"__item_{k}")
        if v is None:
            v = self.cache["_reference"].get_attr("__getitem__")(k)
            v = self._wmo(v)
            self.cache[f"__item_{k}"] = v
        return v

    def __setitem__(self, k, v):
        v = self.cache["_reference"].get_attr("__getitem__")(k)
        v = self._wmo(v)
        self.cache[f"__item_{k}"] = v
        self.cache["_reference"].get_attr("__setattr__")(k, v)

    def __bool__(self):
        return self.cache["_reference"].get_attr("__bool__")()


class ObjectReference:
    """
    This is handles the calls to the reference object so that both
    `MethodCache` and `SmartCache` reference the same object and when one
    resurrects it, the other sees it.
    """

    def __init__(self, reference: Any, resurrect_reference: Optional[Tuple]):
        self.reference = reference
        self.resurrect_reference = resurrect_reference

    def _try_resurrect(self) -> None:
        if self.resurrect_reference is None:
            raise CannotResurrectObject(self)
        else:
            func = self.resurrect_reference[0]
            args = self.resurrect_reference[1:]
            self.reference = func(*args)

    def get_attr(self, name: str) -> Any:
        if self.reference is None:
            pinfo(f"Resurrecting reference object due to call to attribute '{name}'")
            self._try_resurrect()
        return getattr(self.reference, name)

    def __getstate__(self):
        return self.resurrect_reference

    def __setstate__(self, state):
        self.reference = None
        self.resurrect_reference = state

    def __repr__(self):
        return f"ObjectReference({self.reference})"


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

    def __repr__(self):
        ret = "CallableArguments("
        for a in self.args:
            ret += f"{repr(self.args)}, "
        for k, v in self.kwargs.items():
            ret += f"{repr(k)}={repr(v)}, "
        ret += ")"
        return ret


class MethodCache:
    """
    A simple wrapper that checks if the arguments are in the
    cache, otherwise runs the method and caches the arguments
    """

    def __init__(
        self,
        reference: ObjectReference,
        attr_name: str,
        special_method: bool = False,
    ):
        self.reference = reference
        self.name = attr_name
        self.cache = dict()
        self.special_method = special_method

    def _wmo(self, obj):
        return wrap_module_objects(obj, resurrect_reference=None)

    def __call__(self, *args, **kwargs):
        args = list(map(self._wmo, args))
        kwargs = {k: self._wmo(v) for k, v in kwargs.items()}
        call_args = CallableArguments(*args, **kwargs)
        cached_res = self.cache.get(call_args)
        if cached_res is not None:
            return cached_res
        else:
            attr = self.reference.get_attr(self.name)
            if self.special_method:
                args = [arg.cache["_reference"].reference for arg in args]
                kwargs = {k: v.cache["_reference"].reference for k, v in kwargs.items()}
            res = attr(*args, **kwargs)
            res = self._wmo(res)
            self.cache[call_args] = res
            return res


def wrap_module_objects(
    obj: Any,
    resurrect_reference: Optional[Tuple] = None,
):
    """
    Returns the object wrapped with `SmartCache` class if it is not a Cache
    """
    if type(obj) not in [SmartCache, MethodCache]:
        return SmartCache(
            reference=obj,
            resurrect_reference=resurrect_reference,
        )
    else:
        return obj
