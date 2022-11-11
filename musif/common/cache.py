import random
from typing import Any, Dict, List, Optional, Tuple, Union

from deepdiff import DeepHash

from musif.logs import pinfo, pwarn

from .exceptions import CannotResurrectObject, SmartCacheModified


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

    If the object is changed, the change is not cached. As such. only read
    operations can be executed on a ``SmartCache``.

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

    Sometimes, the methods of the referenced object expect a non-cached module,
    for instance when a type checking or a hash comparison is done. For those
    situations, `SmartModuleCache` provides *special methods* that start with
    `SmartModuleCache.SPECIAL_METHODS_NAME` (which defaults to
    `"smartcache__"`). It is possible call any method with
    `smartcache__methodname`, e.g. `score.smartcache__remove`.
    When a special method is called, the first call is performed with the
    non-cached arguments, as it would happen without `SmartModuleCache`.

    NotImplemented: When `smart_pickling` is True, it pickles the dictionary
    alone, without the reference, otherwise, it pickles the reference as well.

    Note: In future, `deepdiff.Delta` could be used to allow in-place
    operations, but it needs that:
        1. the object modified are pickable
        2. the reference are deep-copiable (for some reason, music21 objects)
            sometimes exceed the maximum number of recursion while deep-copying
    """

    SPECIAL_METHODS_NAME = "smartcache__"

    def __init__(
        self,
        reference: Any = None,
        target_addresses: List[str] = ["music21"],
        resurrect_reference: Optional[Tuple] = None,
    ):

        cache: Dict[
            str,
            Union[Tuple, str, int, SmartModuleCache, MethodCache, Any],
        ] = {
            "_hash": random.randint(10**10, 10**15),
            "_target_addresses": target_addresses,
            "_reference": ObjectReference(reference, resurrect_reference),
        }
        object.__setattr__(self, "cache", cache)

    def __isinstancecheck__(self, other):
        return isinstance(self.cache["_reference"].reference, other)

    def __issubclasscheck__(self, other):
        return issubclass(self.cache["_reference"].reference, other)

    def __repr__(self):
        _reference = self.cache["_reference"]
        return f"SmartModuleCache({_reference}, {_module})"

    @property
    def target_addresses(self):
        return self.cache["_target_addresses"]

    @target_addresses.setter
    def target_addresses(self, value):
        self.cache["_target_addresses"] = value

    def __hash__(self):
        return self.cache["_hash"]

    def _wmo(self, obj):
        return wrap_module_objects(
            obj,
            target_addresses=self.cache["_target_addresses"],
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
                target_addresses=self.cache["_target_addresses"],
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
        pwarn(str(SmartCacheModified(self, k)))
        v = self.cache["_reference"].get_attr("__getitem__")(k)
        v = self._wmo(v)
        self.cache[f"__item_{k}"] = v
        self.cache["_reference"].get_attr("__setattr__")(k, v)

    def __bool__(self):
        return self.cache["_reference"].get_attr("__bool__")()


class ObjectReference:
    """
    This is handles the calls to the reference object so that both
    `MethodCache` and `SmartModuleCache` reference the same object and when one
    resurrects it, the other sees it.
    """

    def __init__(self, reference: Any, resurrect_reference: Optional[Tuple]):
        self.reference = reference
        self.resurrect_reference = resurrect_reference
        self.deephash = DeepHash(reference)[reference]

    def _try_resurrect(self) -> None:
        if self.resurrect_reference is None:
            raise CannotResurrectObject(self)
        else:
            func = self.resurrect_reference[0]
            args = self.resurrect_reference[1:]
            self.reference = func(*args)
            self.deephash = DeepHash(self.reference)

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

    def ischanged(self):
        """
        Returns if the reference object is changed using value comparison of
        its attributes recursively.
        """
        newhash = DeepHash(self.reference)[self.reference]
        if newhash != self.deephash:
            return True
        else:
            return False


def __compare_ref(a, b) -> bool:
    """
    Compares two objects by the values of their attributes ricorsively
    """
    a_d = vars(a)
    b_d = vars(b)

    # check that the attribute names are exactly the same
    # keys are strings, so can be compared by hash
    if len(set(a_d.keys()).symmetric_difference(b_d)) > 0:
        return False

    for k, v in a_d.items():
        if not compare_ref(v, b_d[k]):
            return False

    return True


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
        target_addresses: List[str] = ["music21"],
        special_method: bool = False,
    ):
        self.reference = reference
        self.name = attr_name
        self.cache = dict()
        self.target_addresses = target_addresses
        self.special_method = special_method

    def _wmo(self, obj):
        return wrap_module_objects(
            obj, target_addresses=self.target_addresses, resurrect_reference=None
        )

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
            if self.reference.ischanged():
                pwarn(str(SmartCacheModified(self, self.name)))
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
