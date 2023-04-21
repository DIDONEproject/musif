from typing import List
from musif.config import ExtractConfiguration

import contextlib
import os
import tempfile
import subprocess
import pandas as pd

from musif.extract.features.jsymbolic.utils import get_java_path, _jsymbolic_path

JSYMBOLIC_JAR = str(_jsymbolic_path())
JAVA_PATH = get_java_path()


def get_tmpdir():
    if os.path.exists("/dev/shm"):
        return tempfile.TemporaryDirectory(dir="/dev/shm")
    else:
        return tempfile.TemporaryDirectory()


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):
    # 1. create a temporary directory (if Linux, force RAM usig /dev/shm)
    with get_tmpdir() as tmpdirname:
        # 2. convert the score to MEI usiing music21
        # TODO: if music21 implements export to MEI, use it
        midi_path = os.path.abspath(os.path.join(tmpdirname, "score.midi"))
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stdout(devnull):
                score_data['score'].write("MIDI", midi_path)
        # 3. run the MEI file through the jSymbolic jar savign csv into the temporary
        # directory in RAM
        out_path = os.path.abspath(os.path.join(tmpdirname, "features"))
        cmd = [JAVA_PATH,
               f"-Xmx{cfg.jsymbolic_max_ram}",
               "-jar",
               JSYMBOLIC_JAR,
               "-csv",
               ]
        if cfg.jsymbolic_config_file is not None:
            cmd += ["-configrun", cfg.jsymbolic_config_file]
        subprocess.run(
            cmd + [
                midi_path,
                out_path + ".xml",
                out_path + "_def.xml",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        # 4. read the csv file into a pandas dataframe
        df = pd.read_csv(out_path + ".csv", na_values=["NaN", " NaN", "NaN ", " NaN "])
        df = df.drop(columns=df.columns[0])
        # 5. add `js_` prefix to the column names
        df.columns = ["js_" + c for c in df.columns]
        # 6. load the features into the score_features dictionary
        score_features.update(df.to_dict(orient='records')[0])


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):
    pass
