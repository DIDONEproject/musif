#%%
import os
import subprocess
import sys
from math import floor
from os import path
from pathlib import Path

from music21.stream.base import Measure, Score

import musif.extract.constants as C
from musif.extract.extract import parse_filename
from musif.logs import perr, pinfo, pwarn

sys.path.append(os.path.abspath('.'))
from feature_extraction.custom_conf import CustomConf
from feature_extraction.utils import get_ariaid

#%%

def cut_by_measures_theme_A(cfg, data):
    score_id = get_ariaid(path.basename(data[C.DATA_FILE]))
    score: Score = data[C.DATA_SCORE]
    last_measure = 1000000
    for d in cfg.scores_metadata[last_measure]:
        if d["Id"] == score_id:
            last_measure = floor(float(d.get(cfg.end_of_theme_a, last_measure)))
            if last_measure == 0:
                name = data['file'].name
                pwarn(f'Last measure for {name} fil was found to be 0! Remember to update metadata before extraction ;) Setting last measure to the end of the score.\n')
                last_measure = 1000000
            break

    remove_everything_after_measure(score, last_measure)

def remove_everything_after_measure(score, last_measure):
    for part in score.parts:
        read_measures = 0
        elements_to_remove = []
        for measure in part.getElementsByClass(Measure):
            read_measures += 1
            if read_measures > last_measure:
                elements_to_remove.append(measure)
        part.remove(targetOrList=elements_to_remove)

def save_xml(data, new_filename):
    new_filename = str(new_filename) + '.xml'
    data[C.DATA_SCORE].write('musicxml', fp=f'{new_filename}')
    
def save_to_midi(filename):
    filename = str(filename)
    new_filename = filename + '.mid'
    if path.exists(new_filename):
            pinfo(f"{filename} already exists as MIDI, skipping it!")
            return
    cmd = ["mscore", "-fo", new_filename, filename + '.xml']
    pinfo(f"Converting {filename} to MIDI")
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        pwarn(
            f"Continuing because time expired for file {filename}! Try running:\n"
            + "".join(cmd)
        ) 
#%%

didone_config = "feature_extraction/config_extraction.yml"

cfg = CustomConf(didone_config)
data_path = 'data/xml/'
data_path_cutted = Path('data/xml/cutted_themeA/')

#%%

for filename in sorted(Path(data_path).glob(f"*.xml")):
        data = {}
        new_filename = data_path_cutted / Path(filename.stem + '_cutted')
        if path.exists(str(new_filename) + '.xml'):
            pinfo(f"{filename} already exists as cutted xml, skipping it!")
            continue
        score = parse_filename(
            filename,
            cfg.split_keywords,
            expand_repeats=cfg.expand_repeats,
            export_dfs_to=None,
            remove_unpitched_objects=cfg.remove_unpitched_objects,
        )
        data[C.DATA_SCORE] = score
        data[C.DATA_FILE] = filename
        cut_by_measures_theme_A(cfg, data)
        data_path_cutted.mkdir(exist_ok=True)
        try:        
            save_xml(data, new_filename)
        except Exception as e:
            perr(f'There was an error saving score {filename} to xml: {e}. Skipping it!')
            continue
        try:        
            save_to_midi(new_filename)
        except Exception as e:
            perr(f'There was an error saving score {filename} to midi: {e}. Skipping it!')
