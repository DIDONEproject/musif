"""
This module contains functionality to use the MuseScore program as a
backend for loading and rendering scores.

Most  of this code was shared from `partitura` module developed by JKU CP team
and the ERC project "Whither Music?"

https://github.com/CPJKU/partitura/blob/b8f1fb8af97e3237c73e860c2bee679e1e0c79c7/partitura/io/musescore.py


"""

import platform
import shutil
import subprocess
from pathlib import PurePath
from tempfile import NamedTemporaryFile
from typing import Union

from music21.stream import Score
from music21.converter import parse

from musif.common.exceptions import ParseFileError

class MuseScoreNotFoundException(Exception):
    pass


class FileImportException(Exception):
    pass


_MSCORE_EXEC = ""


def find_musescore3():

    result = shutil.which("musescore")

    if result is None:
        result = shutil.which("musescore3")

    if result is None:
        result = shutil.which("mscore")

    if result is None:
        result = shutil.which("mscore3")

    if result is None:
        if platform.system() == "Linux":
            pass

        elif platform.system() == "Darwin":

            result = shutil.which("/Applications/MuseScore 3.app/Contents/MacOS/mscore")

        elif platform.system() == "Windows":
            result = shutil.which(r"C:\Program Files\MuseScore 3\bin\MuseScore.exe")

    global _MSCORE_EXEC
    _MSCORE_EXEC = result
    return result


find_musescore3()


def load_via_musescore(
    filename: Union[str, PurePath],
) -> Score:
    """Load a score through through the MuseScore program.
    This function attempts to load the file in MuseScore, export it as
    MusicXML, and then load the MusicXML. This should enable loading
    of all file formats that for which MuseScore has import-support
    (e.g. MIDI, and ABC, but currently not MEI).

    Parameters
    ----------
    """

    if _MSCORE_EXEC == "":

        raise MuseScoreNotFoundException()

    with NamedTemporaryFile(suffix=".xml") as xml_fh:

        cmd = [_MSCORE_EXEC, "-o", xml_fh.name, filename]

        try:

            ps = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

            if ps.returncode != 0:

                raise FileImportException(
                    (
                        "Command {} failed with code {}. MuseScore "
                        "error messages:\n {}"
                    ).format(cmd, ps.returncode, ps.stderr.decode("UTF-8"))
                )
            score = parse(xml_fh.name)

        except Exception as e:
            raise ParseFileError(filename, str(e))
        return score
