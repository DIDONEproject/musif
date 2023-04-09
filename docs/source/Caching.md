# Caching

`musif` is entirely written using [`music21`](https://web.mit.edu/music21/) objects for
computing features. This approach allows users to easily add features using a python
library that is largely supported by the community. However, it doesn't come without
issues.

We have mainly found two weaknesses in this approach:
1. While `music21` is doing a great job at improving performances, it remains slow when
   iterating over complex and deeply nested objects and even more slow while parsing
   large MusicXML files.
2. `music21` still has various issues about serializing data, including pickling and
   deepcopying.

For this reason, we have implemented a system for automatic caching `music21` objects in a
serializable format. The only drawback of our system is that it is not possible to use
the cached objects for writing data, but only for reading. Put in simple words, if you
decide to use the cache system, you cannot modify any `music21` object from inside the
features.

## What you can do with the caching system

The cache system is implemented in the package `musif.cache`. It allows you to:
1. pickle the files, saving the time needed for parsing
2. cache every call to expensive `music21` function
3. expand your code basis using cached properties

In our experiments we have obtained a code around 2-3 times faster when using the cache.

Once you have cached your objects, you can use them with the existing properties; if you
change them, for instance running a wrong code, you will have to delete them to get 
the original results back.

If you try to access a property that is not cached, the caching system will try to parse
the file from where that property may be available.

## Interacting with cache objects

The cache objects are essentially `SmartModuleCache` objects. They behave exactly as the
cached object, but store the returned values in a property named `cache`. When using
`SmartModuleCache` interactivly you can look at `cache.keys()` for inspecting it.

Most of the values stored inside the `cache` dictionary will be other `SmartModuleCache`
or `MethodCache` objects. `MethodCache` are special objects that are used to cache the calls to
methods, similarly to the standard `lru_cache`, but with the ability of pickling them.
To this purpose, we use the `deephash` module, which computes a fixed hash based on the
content of the objects. However, since `music21` objects are often deeply nested, `deephash`
would be slow. As such, `SmartModuleCache` objects implement their own hashing function
as well. Note that, for now, `SmartModuleCache` objects implement a weak hash, which is in
no way proven to be effective for situations where many objects interact.

Another feature that you should be aware of is that `SmartModuleCache` transforms any
iterator to lists and make it available under the `__list__` field. The successive calls
to the iterator will then return the list.

## Modifying `music21` objects before of caching

The only condition for using the cache system is that you do not change the `music21`
objects from inside the features. If you are doing it,
you should probably stop doing so, because it necessarily involves a copy of the
`music21` objects, which is slow.

To allow you to modify the parsed score, we have introduced the option of using hooks,
as explained [here](./Hooks.html).
