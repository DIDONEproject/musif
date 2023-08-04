import logging
import random
import weakref
from typing import Any, Dict, List, Optional, Tuple, Union

from deepdiff import DeepHash, deephash

from musif.common.exceptions import CannotResurrectObject, SmartCacheModified
from musif.logs import pinfo, pwarn

deephash.logger.setLevel(logging.ERROR)

CACHE_FILE_EXTENSION = ".pkl"


class ObjectReference:
    """
    This handles the calls to the reference object so that both
    `MethodCache` and `SmartModuleCache` reference the same object and when one
    resurrects it, the other sees it.
    """

    __slots__ = ("reference", "resurrect_reference", "parent", "name", "args")

    def __init__(
        self,
        reference: Any,
        resurrect_reference: Optional[Tuple],
        parent=None,
        name: str = "",
        args: Optional[Tuple] = None,
    ):
        self.reference = reference
        self.resurrect_reference = resurrect_reference
        self.parent = parent
        self.name = name
        self.args = args
        # self.deephash = DeepHash(reference)[reference]

    def _try_resurrect(self) -> None:
        if self.resurrect_reference is None:
            if self.parent is None:
                raise CannotResurrectObject(self)
            else:
                origin = self.parent
                for i in range(len(self.name)):
                    if self.name[i] == "":
                        raise CannotResurrectObject(self)
                    if isinstance(origin, ObjectReference):
                        origin = origin.get_attr(self.name[i])
                    else:
                        origin = getattr(origin, self.name[i])
                    if self.args[i] is not None:
                        origin = origin(*self.args[i])
                self.reference = origin

        else:
            func = self.resurrect_reference[0]
            args = self.resurrect_reference[1:]
            pinfo(f"Resurrecting via function call: {func}{args}")
            self.reference = func(*args)
            # self.deephash = DeepHash(self.reference)

    def get_attr(self, name: str) -> Any:
        if not hasattr(self, "reference") or self.reference is None:
            # pinfo(f"Resurrecting reference object due to call to attribute '{name}'")
            # traceback = __import__('traceback')
            # traceback.print_list(
            #     [f for f in traceback.extract_stack() if "musif" in f.filename]
            # )
            self._try_resurrect()
        return getattr(self.reference, name)

    def __getstate__(self):
        return dict(
            resurrect_reference=self.resurrect_reference,
            parent=self.parent,
            name=self.name,
            args=self.args,
        )

    def __setstate__(self, state):
        self.reference = None
        self.resurrect_reference = state["resurrect_reference"]
        self.parent = state["parent"]
        self.name = state["name"]
        self.args = state["args"]

    def __repr__(self):
        return f"ObjectReference({self.reference}, {self.name})"


class _MyNone:
    """Type used internally for representing attributes that do not exist in the
    reference object"""

    pass


class SmartModuleCache:
    """
    This class wraps any object so that its function calls can be cached in a
    dict, very similarly to how `functools.lru_cache` works.

    The object keeps a dictionary and a reference to the wrapped object.
    Each time a method, a field, or a property is called, it stores the result
    value in the dictionary.
    When the same call is performed a second time, the result value is taken
    from the dictionary.

    If the object is changed, the change is not cached. As such, only read
    operations can be executed on a ``SmartModuleCache``.

    After unpickling, the referenced object is no longer available.
    If `resurrect_reference` is not None, it will be loaded using its value. In
    such a case, `resurrect_reference` should be a tuple with a function in the
    first position and the arguments later; the function returned value must be
    the reference object.

    If the method/property/field returns an object defined in a
    one of the `target_addresses`, this class will return a wrapped version of
    that object.
    In `musif`, this is used to wrap all the music21 objects and to cache
    (most of) music21 operations.

    When a method is called, it is matched with all the arguments, similarly to
    `functools.lru_cache`, thus using the hash value of the objects.

    When pickled, this object only pickles the cache dictionary.
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

    Note: this class implements `__repr__` in a custom way, while proxies the
    `__str__` method to the referenced object.

    Note: In future, `deepdiff.Delta` could be used to allow in-place
    operations, but it needs that:
        
    1. the object modified are pickable
    2. the reference are deep-copiable (for some reason, music21 objects)
        sometimes exceed the maximum number of recursion while deep-copying
    """

    __slots__ = "cache"
    SPECIAL_METHODS_NAME = "smartcache__"

    def __init__(
        self,
        reference: Any = None,
        resurrect_reference: Optional[Tuple] = None,
        parent: Optional[ObjectReference] = None,
        name: Tuple[str] = ("",),
        args: Tuple[Optional[Tuple]] = (None,),
        target_addresses: List[str] = ["music21"],
        check_reference_changes: bool = False,
    ):

        cache: Dict[
            str,
            Union[Tuple, str, int, SmartModuleCache, MethodCache, Any],
        ] = {
            "_hash": random.randint(10**10, 10**15),
            "_target_addresses": target_addresses,
            "_reference": ObjectReference(
                reference, resurrect_reference, parent, name, args
            ),
            "_check_reference_changes": check_reference_changes,
            "_type": type(reference),
        }
        object.__setattr__(self, "cache", cache)

    def smartforcecache(self, name, *args, **kwargs):
        """
        This method can be used to forcedly cache some attribute of the reference
        object without using it. `name` is the name of the attribute. If it is a method,
        `*args` and `**kwargs`.

        Return `(True, None)` if object is cached, `(False, Exception)` otherwise
        """
        try:
            attr = self.__getattr__(name)
            assert self.cache["name"] is not None, "Object retrieved but not cached!"

            if isinstance(attr, MethodCache):
                attr.__forcecache(*args, **kwargs)
        except Exception as e:
            return False, e
        return True, None

    def __repr__(self):
        _reference = self.cache["_reference"]
        _addresses = self.cache["_target_addresses"]
        _class = self.__class__.__qualname__
        return f"{_class}({_reference}, {_addresses})"

    def __str__(self):
        s = self.cache.get("__str__")
        if s is None:
            s = str(self.cache["_reference"].reference)
            self.cache["__str__"] = s
        return s

    @property
    def target_addresses(self):
        return self.cache["_target_addresses"]

    @target_addresses.setter
    def target_addresses(self, value):
        self.cache["_target_addresses"] = value

    def __hash__(self):
        return self.cache["_hash"]

    def _wmo(self, obj, name=("",), args=(None,)):
        from .utils import wrap_module_objects
        return wrap_module_objects(
            obj,
            target_addresses=self.cache["_target_addresses"],
            resurrect_reference=None,
            parent=self.cache["_reference"],
            name=name,
            args=args,
        )

    def __getattr__(self, name: str) -> Any:
        """
        The real key of this class is this method!
        """
        attr = self.cache.get(name)
        if attr is None:
            # attr not in cache
            attr = self._get_new_attr(name)
            if attr is None:
                attr = _MyNone
            self.cache[name] = attr
        if attr is _MyNone:
            return None
        else:
            return attr

    def __delattr__(self, name):
        del self.cache[name]

    def __setattr__(self, name, value):
        pwarn(
            "You are using a music21 object in writing mode! consider change your code so that SmartModuleCache works correctly. See the stack-trace:"
        )
        # traceback = __import__('traceback')
        # traceback.print_list(
        #     [f for f in traceback.extract_stack() if "musif" in f.filename]
        # )
        if self.cache["_reference"].reference is not None:
            self.cache["_reference"].get_attr("__setattr__")(name, value)

    def _get_new_attr(self, name: str) -> Any:
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
                check_reference_changes=self.cache["_check_reference_changes"],
            )
        else:
            # cache the value and returns it
            attr = self._wmo(attr, (name,))

        return attr

    def __setstate__(self, state):
        object.__setattr__(self, "cache", state)

    def __getstate__(self):
        return self.cache

    # caching other special methods
    def __list__(self, idx=None):
        it = self.cache.get("__list__")
        if it is None:
            it = self.cache["_reference"].get_attr("__iter__")()
            it = [
                self._wmo(
                    x,
                    ("__getitem__",),
                    ((i,),),
                )
                for i, x in enumerate(it)
            ]
            self.cache["__list__"] = it
        if idx is not None:
            return it[idx]
        else:
            return it

    def __iter__(self):
        return iter(self.__list__())

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
            v = self._wmo(v, ("__getitem__",), ((k,),))
            self.cache[f"__item_{k}"] = v
        return v

    def __setitem__(self, k, v):
        pwarn(
            "You are using a music21 object in writing mode! consider change your code so that SmartModuleCache works correctly. See the stack-trace:"
        )
        # traceback = __import__('traceback')
        # traceback.print_list(
        #     [f for f in traceback.extract_stack() if "musif" in f.filename]
        # )
        try:
            v = self.cache["_reference"].get_attr("__getitem__")(k)
        except KeyError:
            pass
        v = self._wmo(v, ("__setitem__",), ((k, v),))
        self.cache[f"__item_{k}"] = v
        self.cache["_reference"].get_attr("__setattr__")(k, v)

    def __bool__(self):
        b = self.cache.get("__bool__")
        if b is None:
            try:
                b = self.cache["_reference"].get_attr("__bool__")()
            except AttributeError:
                b = self.cache["_reference"].reference is not None
            finally:
                self.cache["__bool__"] = b
        return b

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


class CallableArguments:
    """
    This class represents a set of ordered arguments.
    The hash is the concatenation of the argument hashes.
    If the arguments are SmartModuleCache objects, this object uses their cache (which
    persists to disk), otherwise it uses `deepdiff.DeepHash` to compute a hash based on
    the content value (which should persists across pickling).

    Note that `DeepHash` may be much slower than the builtin `hash()` function,
    so for large and complex objects like `music21.Score`, just use a
    `SmartModuleCache` wrapper.
    """

    def __init__(self, *args, **kwargs):
        self.args = []
        self.kwargs = {}

        # removing weakreferences (cannot be pickled)
        for arg in args:
            if isinstance(arg, weakref.ReferenceType):
                __import__('ipdb').set_trace()
                self.args.append(arg())
            else:
                self.args.append(arg)

        for k, v in kwargs.items():
            if isinstance(k, weakref.ReferenceType):
                __import__('ipdb').set_trace()
                k = k()
            if isinstance(v, weakref.ReferenceType):
                __import__('ipdb').set_trace()
                v = v()
            kwargs[k] = v

        h = ""

        # hashing SmartModuleCache
        for arg in self.args:
            if type(arg) is SmartModuleCache:
                h += str(hash(arg))

        kwargs_keys = sorted(self.kwargs.keys())
        for k in kwargs_keys:
            v = self.kwargs[k]
            if type(v) is SmartModuleCache:
                h += str(hash(v))

        # hashing other object types by value
        all_args = (self.args, self.kwargs)
        h += DeepHash(all_args, exclude_types=[SmartModuleCache])[all_args]

        self._hash = int(h, 16)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if type(other) is CallableArguments:
            return other._hash == self._hash
        else:
            return False

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

    __slots__ = (
        "reference",
        "name",
        "cache",
        "target_addresses",
        "special_method",
        "check_reference_changes",
    )

    def __init__(
        self,
        reference: ObjectReference,
        attr_name: str,
        target_addresses: List[str] = ["music21"],
        special_method: bool = False,
        check_reference_changes: bool = False,
    ):
        self.reference = reference
        self.name = attr_name
        self.cache = dict()
        self.target_addresses = target_addresses
        self.special_method = special_method
        self.check_reference_changes = check_reference_changes

    def _wmo(self, obj, args=None):
        from .utils import wrap_module_objects
        return wrap_module_objects(
            obj,
            target_addresses=self.target_addresses,
            resurrect_reference=None,
            parent=self.reference,
            name=(self.name,),
            args=(args,),
        )

    def __call__(self, *args, **kwargs):
        args = list(map(self._wmo, args))
        kwargs = {k: self._wmo(v) for k, v in kwargs.items()}
        call_args = CallableArguments(*args, **kwargs)
        cached_res = self.cache.get(call_args)
        if cached_res is not None:
            if cached_res is _MyNone:
                return None
            return cached_res
        else:
            attr = self.reference.get_attr(self.name)
            if self.special_method:
                args = [arg.cache["_reference"].reference for arg in args]
                kwargs = {k: v.cache["_reference"].reference for k, v in kwargs.items()}
            res = attr(*args, **kwargs)
            if res is None:
                # caching _MyNone and returning None
                self.cache[call_args] = _MyNone
            else:
                res = self._wmo(res, args=(*args, *kwargs.values()))
                self.cache[call_args] = res
            if self.check_reference_changes and self.reference.ischanged():
                pwarn(str(SmartCacheModified(self, self.name)))
            return res

    def smartforcecache(self, *args, **kwargs):
        self.__call__(*args, **kwargs)
        assert (
            self.cache.get(CallableArguments(*args, **kwargs)) is not None
        ), "Method retrieved but arguments not cached!"
