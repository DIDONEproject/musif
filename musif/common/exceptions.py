class MissingFileError(Exception):
    """Exception informing that an expected file couldn't be found."""

    def __init__(self, file_path: str):
        super().__init__(f"File with path '{file_path}' couldn't be found")


class ParseFileError(Exception):
    """Exception informing that a file couldn't be parsed with the specified attributes."""

    def __init__(self, file_path: str):
        super().__init__(f"Parse error with file '{file_path}'")


class CannotResurrectObject(Exception):
    """Exception raised when a cached object is accessed on a non-cached attribute and the object doesn't know how to resurrect the non-cached object"""

    def __init__(self, obj):
        super().__init__(
            f"Cannot resurrect object {repr(obj)}, please define a `resurrect_reference` field"
        )


class SmartCacheModified(Exception):
    """Exception raised when trying to modify the reference of a `SmartCache` object"""

    def __init__(self, obj, attr):
        super().__init__(f"Cannot modify SmartCache {obj}, via attribute {attr}")


class FeatureError(RuntimeError):
    """Exception raised when computing one of the features modules"""

    pass
