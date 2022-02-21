import re
from typing import List

from musif.extract.features.interval.constants import (
    INTERVAL_COUNT, TRIMMED_INTERVALLIC_MEAN)
from musif.extract.features.scale.constants import DEGREE_PREFIX
from musif.logs import pinfo
from pandas import DataFrame

from .constants import PRESENCE


def replace_nans(df):
    for col in df.columns:
        INTERVAL_COUNT
        if '_Interval' in col or col.startswith('Key_') or col.startswith('Chord_') or col.startswith('Chords_') or col.startswith('Additions_') or col.startswith('Numerals_') or col.endswith('_DottedRhythm') or col.endswith('_DoubleDottedRhythm')  or '_Degree' in col or TRIMMED_INTERVALLIC_MEAN in col or PRESENCE in col:
            df[col]= df[col].fillna(0)

def join_part_degrees(total_degrees: List[str], part: str, df: DataFrame):
    part_degrees=[i for i in total_degrees if part in i]

    aug=[i for i in part_degrees if '#' in i]
    desc=[i for i in part_degrees if 'b' in i and not 'bb' in i]
    d_desc=[i for i in part_degrees if 'bb' in i]
    d_asc=[i for i in part_degrees if 'x' in i]

    pattern='^'+part+'Degree'+'[0-9].*'
    degree_nat = [x for x in part_degrees if re.search(pattern, x)]
    degree_nonat = [i for i in part_degrees if i not in degree_nat]

    df[part+DEGREE_PREFIX+'_Aug']=df[aug].sum(axis=1)
    df[part+DEGREE_PREFIX+'_Desc']=df[desc].sum(axis=1)
    df[part+DEGREE_PREFIX+'_Dasc']=df[d_asc].sum(axis=1)
    df[part+DEGREE_PREFIX+'_Ddesc']=df[d_desc].sum(axis=1)
    df[part+DEGREE_PREFIX+'_Nat']=df[degree_nat].sum(axis=1)
    df[part+DEGREE_PREFIX+'_Nonat']=df[degree_nonat].sum(axis=1)

def log_errors_and_shape(composer_counter: list, novoices_counter: list, duetos_counter: list, df: DataFrame):
    pinfo("\nTotal files skipped by composer: ", len(composer_counter))
    pinfo(composer_counter)
    pinfo("\nTotal files skipped by no-voices: ", len(novoices_counter))
    pinfo(novoices_counter)
    pinfo("\nTotal files skipped by duetos/trietos: ", len(duetos_counter))
    pinfo(duetos_counter)
    pinfo("\nFinal shape of the DataFrame: ", df.shape)



