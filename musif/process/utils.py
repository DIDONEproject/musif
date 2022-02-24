import re
from typing import List
import numpy as np
import pandas as pd
from tqdm import tqdm
from musif.extract.features.ambitus.constants import HIGHEST_NOTE_INDEX, LOWEST_NOTE_INDEX
from musif.extract.features.harmony.constants import KEY_MODULATORY, KEY_PERCENTAGE, KEY_prefix

from musif.extract.features.interval.constants import (
    INTERVAL_COUNT, TRIMMED_INTERVALLIC_MEAN)
from musif.extract.features.prefix import get_part_prefix
from musif.extract.features.scale.constants import DEGREE_PREFIX
from musif.extract.features.scoring.constants import VOICES
from musif.logs import pinfo
from pandas import DataFrame
from .constants import PRESENCE, voices_list_prefixes


def replace_nans(df):
    for col in df.columns:
        INTERVAL_COUNT
        if '_Interval' in col or col.startswith('Key_') or col.startswith('Chord_') or col.startswith('Chords_') or col.startswith('Additions_') or col.startswith('Numerals_') or col.endswith('_DottedRhythm') or col.endswith('_DoubleDottedRhythm')  or '_Degree' in col or TRIMMED_INTERVALLIC_MEAN in col or PRESENCE in col:
            df[col]= df[col].fillna(0)

def merge_duetos_trios(df: DataFrame, generic_sound_voice_prefix: str)-> None:
    pinfo('\nCalculating duetos and trietos:\n')
    for index in df[df[VOICES].str.contains(',')].index:
        all_voices = df[VOICES][index].split(',')
        voice_cols = [col for col in df.columns.values if any(voice in col for voice in voices_list_prefixes) and not pd.isnull(df.iloc[index][col])]
        first_voice = all_voices[0]
        columns_to_merge=[i for i in voice_cols if first_voice in i.lower()]
        for col in tqdm(columns_to_merge):
            formatted_col = col.replace(get_part_prefix(first_voice), generic_sound_voice_prefix)
            similar_cols = []
            for j in range(0, len(all_voices)):
                similar_col=col.replace(get_part_prefix(first_voice),get_part_prefix(all_voices[j]))
                if similar_col in df:
                    similar_cols.append(similar_col)
            if isinstance(df.loc[index,similar_cols][0], (int, float)):
                if HIGHEST_NOTE_INDEX in col or ('Largest' and 'Asc') in col:
                    df[formatted_col]=df.loc[index,similar_cols].max()
                elif LOWEST_NOTE_INDEX in col or ('Largest' and 'Desc') in col:
                    df[formatted_col]=df.loc[index,similar_cols].min()
                else:
                    df[formatted_col]=df.loc[index,similar_cols].mean()
            else:
                df[formatted_col]=np.nan
                
            df.loc[index,similar_cols]=np.nan

def merge_single_voices(df: DataFrame, generic_sound_voice_prefix: str) -> None:
    pinfo('\nJoining voice parts...')
    for col in df.columns.values:
            if any(voice in col for voice in voices_list_prefixes):
                formatted_col=col
                for voice_prefix in voices_list_prefixes:
                    formatted_col = formatted_col.replace(voice_prefix, generic_sound_voice_prefix)
                if formatted_col in df:
                    df[formatted_col].fillna(df[col], inplace=True)
                else:
                    df[formatted_col]=df[col]
                df.drop(col, axis=1, inplace=True)
                
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

def log_errors_and_shape(composer_counter: list, novoices_counter: list, df: DataFrame):
    pinfo(f"\nTotal files skipped by composer: {len(composer_counter)}")
    pinfo(str(composer_counter))
    pinfo(f"\nTotal files skipped by no-voices: { len(novoices_counter)}")
    pinfo(str(novoices_counter))
    # pinfo(f"\nTotal files skipped by duetos/trietos: {len(duetos_counter)}")
    # pinfo(str(duetos_counter))
    pinfo(f"\nFinal shape of the DataFrame: {df.shape}")

def delete_previous_items(df):
    errors=pd.read_csv('errors.csv', low_memory=False, sep='\n', encoding_errors='replace',header=0)['FileName'].tolist()
    for item in errors:
        index = df.index[df['FileName']==item]
        df.drop(index, axis=0, inplace=True)

def join_keys(df: DataFrame):
        key_SD = [KEY_prefix+'IV'+KEY_PERCENTAGE, KEY_prefix+'II'+KEY_PERCENTAGE, KEY_prefix+'VI'+KEY_PERCENTAGE]
        key_sd = [KEY_prefix+'iv'+KEY_PERCENTAGE, KEY_prefix+'ii'+KEY_PERCENTAGE]
        key_tonic = [KEY_prefix+'I'+KEY_PERCENTAGE, KEY_prefix+'i'+KEY_PERCENTAGE]
        key_rel = [KEY_prefix+'III'+KEY_PERCENTAGE, KEY_prefix+'vi'+KEY_PERCENTAGE]

        total_key=key_rel+key_tonic+key_sd+key_SD
        others_key=[i for i in df.columns if KEY_prefix in i and i not in total_key and KEY_MODULATORY not in i]

        df[KEY_prefix+'SD'+KEY_PERCENTAGE]=df[key_SD].sum(axis=1)
        df[KEY_prefix+'sd'+KEY_PERCENTAGE]=df[key_sd].sum(axis=1)
        df[KEY_prefix+'SubD'+KEY_PERCENTAGE]=df[KEY_prefix+'sd'+KEY_PERCENTAGE] + df[KEY_prefix+'SD'+KEY_PERCENTAGE]
        df[KEY_prefix+'T'+KEY_PERCENTAGE] = df[key_tonic].sum(axis=1)
        df[KEY_prefix+'rel'+KEY_PERCENTAGE] = df[key_rel].sum(axis=1)
        df[KEY_prefix+'Other'+KEY_PERCENTAGE] = df[others_key].sum(axis=1)
        # df.drop(total_key+others_key, axis = 1, inplace=True)

def join_keys_modulatory(df: DataFrame):
        key_SD=[KEY_prefix+KEY_MODULATORY+'IV',KEY_prefix+KEY_MODULATORY+'II', KEY_prefix+KEY_MODULATORY+'VI']
        key_sd=[KEY_prefix+KEY_MODULATORY+'iv',KEY_prefix+KEY_MODULATORY+'ii']
        key_tonic=[KEY_prefix+KEY_MODULATORY+'I',KEY_prefix+KEY_MODULATORY+'i']
        key_rel=[KEY_prefix+KEY_MODULATORY+'III',KEY_prefix+KEY_MODULATORY+'vi']

        total_key_mod=key_rel+key_tonic+key_sd+key_SD
        others_key_mod=[i for i in df.columns if KEY_prefix+KEY_MODULATORY in i and i not in total_key_mod]

        df[KEY_prefix+KEY_MODULATORY+'SD']=df[key_SD].sum(axis=1)
        df[KEY_prefix+KEY_MODULATORY+'sd']=df[key_sd].sum(axis=1)
        df[KEY_prefix+KEY_MODULATORY+'SubD']=df[KEY_prefix+KEY_MODULATORY+'sd'] + df[KEY_prefix+KEY_MODULATORY+'SD']
        df[KEY_prefix+KEY_MODULATORY+'T'] = df[key_tonic].sum(axis=1)
        df[KEY_prefix+KEY_MODULATORY+'rel'] = df[key_rel].sum(axis=1)
        df[KEY_prefix+KEY_MODULATORY+'Other'] = df[others_key_mod].sum(axis=1)
        # df.drop(total_key_mod+others_key_mod, axis = 1, inplace=True)

