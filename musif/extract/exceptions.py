class MissingFileError(Exception):
    """Exception informing that an expected file couldn't be found."""

    def __init__(self, file_path: str):
        super().__init__(f"File with path '{file_path}' couldn't be found")


class ParseFileError(Exception):
    """Exception informing that an file couldn't be parsed with the specified attributes."""

    def __init__(self, file_path: str, reason: str):
        super().__init__(f"Parse error with file '{file_path}': {reason}")
