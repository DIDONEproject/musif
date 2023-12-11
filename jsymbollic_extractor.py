

from os import path
from pathlib import Path
import subprocess
from venv import logger
from music21.stream.base import Score
from musif.extract.extract import parse_filename
import musif.extract.constants as C
from musif.logs import pwarn

import sys
import os
sys.path.append(os.path.pardir)
from feature_extraction.custom_conf import CustomConf
from feature_extraction.utils import get_ariaid


def cut_by_measures_theme_A(cfg, data):
    aria_id = get_ariaid(path.basename(data[C.DATA_FILE]))
    score: Score = data[C.DATA_SCORE]
    last_measure = 1000000
    for d in cfg.scores_metadata[cfg.theme_a_metadata]:
        if d["Id"] == aria_id:
            last_measure = floor(float(d.get(cfg.end_of_theme_a, last_measure)))
            if last_measure == 0:
                name = data['file'].split('/')[-1]
                pwarn(f'Last measure for {name} fil was found to be 0! Remember to update metadata before extraction ;) Setting last measure to the end of the score.\n')
                last_measure = 1000000
            break

    # removing everything after end of theme A
    for part in score.parts:
        read_measures = 0
        elements_to_remove = []
        for measure in part.getElementsByClass(Measure):  # type: ignore
            read_measures += 1
            if read_measures > last_measure:
                elements_to_remove.append(measure)
        part.remove(targetOrList=elements_to_remove)  # type: ignore
    if cfg.is_requested_musescore_file() and data[C.DATA_MUSESCORE_SCORE] is not None:
        data[C.DATA_MUSESCORE_SCORE] = data[C.DATA_MUSESCORE_SCORE].loc[
            data[C.DATA_MUSESCORE_SCORE]["mn"] <= last_measure
        ]
        data[C.DATA_MUSESCORE_SCORE].reset_index(inplace=True, drop=True)

def save_xml(data, new_filename):
    data[C.DATA_SCORE].write('musicxml', fp='file.xml')
    
def save_to_midi(filename):
    if filename.with_suffix(".mid").exists():
            logger.info(f"{filename} already exists as MIDI, skipping it!")
            return
    cmd = ["mscore", "-fo", filename.with_suffix(".mid"), filename]
    logger.info(f"Converting {filename} to MIDI")
    try:
        subprocess.run(
            cmd,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        logger.warning(
            f"Continuing because time expired for file {filename}! Try running:\n"
            + "".join(cmd)
        )
            

didone_config = "../feature_extraction/config_extraction.yml"

cfg = CustomConf(didone_config)
data_path = '../data/xml'

for filename in Path(data_path).glob(f"*.xml"):
        data = {}
        score = parse_filename(
            filename,
            cfg.split_keywords,
            expand_repeats=cfg.expand_repeats,
            export_dfs_to=None,
            remove_unpitched_objects=cfg.remove_unpitched_objects,
        )
        data[C.DATA_SCORE] = score
        cut_by_measures_theme_A(cfg, data)
        new_filename = filename.strip('.')[0] + '_cutted' + '.xml'
        save_xml(data, new_filename)
        save_to_midi(new_filename)