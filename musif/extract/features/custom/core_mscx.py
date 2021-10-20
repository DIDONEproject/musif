from functools import lru_cache
from musif.common.constants import RESET_SEQ, get_color
from os import path
from pathlib import Path
from typing import List, Optional
import ms3

from music21.analysis.discrete import Ambitus
import pandas as pd

from musif.config import Configuration
from musif.musicxml import get_intervals, get_notes_and_measures, get_notes_lyrics

from musif.musicxml import (MUSESCORE_FILE_EXTENSION, MUSICXML_FILE_EXTENSION, split_layers)

#TODO: Check if this cache works in different runs. If not, create our own cache to store parsing of previous scores 
@lru_cache(maxsize=None, typed=False)
def parse_score(mscx_file: str, cfg: Configuration):
    cfg.read_logger.info(get_color('INFO')+'\nParsing mscx file... {0}'.format(mscx_file) + RESET_SEQ)
    print('\nParsing mscx file... {0}'.format(mscx_file))

    msc3_score = ms3.score.Score(mscx_file.strip(), logger_cfg={'level': 'ERROR'})
    harmonic_analysis = msc3_score.mscx.expanded
    if harmonic_analysis is None:
        raise Exception('Not able to extract chords from the .mscx file!')
    mn = ms3.parse.next2sequence(msc3_score.mscx.measures.set_index('mc').next)
    mn = pd.Series(mn, name='mc_playthrough')
    harmonic_analysis = ms3.parse.unfold_repeats(harmonic_analysis,mn)
    return harmonic_analysis

def find_mscx_file(musicxml_file: str) -> Optional[Path]:
    return musicxml_file.replace(MUSICXML_FILE_EXTENSION, MUSESCORE_FILE_EXTENSION)

def update_score_objects(score_data: dict, parts_data: List[dict], cfg: Configuration, parts_features: List[dict], score_features: dict):
    mscx_file = find_mscx_file(score_data['file'])
    score_data["mscx_path"] = mscx_file

    file_path = cfg.musescore_dir + mscx_file if cfg.musescore_dir != cfg.data_dir else mscx_file
    try:
        if path.exists(file_path):
            score_data['MS3_score'] = parse_score(score_data['mscx_path'], cfg)
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        cfg.read_logger.warning(get_color('WARNING')+"\nMusescore file was not found for {} file!\nNo harmonic analysis will be extracted.{}".format(mscx_file, RESET_SEQ))

def update_part_objects(score_data: dict, part_data: dict, cfg: Configuration, part_features: dict):
    pass