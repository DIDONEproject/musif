from logging.config import dictConfig
import re
from typing import List

import numpy as np
import pandas as pd
from musif.config import ENDSWITH, INSTRUMENTS_TO_DELETE, STARTSWITH, SUBSTRING_TO_DELETE
from musif.extract.features.core.constants import FILE_NAME
from musif.extract.features.harmony.constants import CHORD_prefix
from musif.extract.features.texture.constants import TEXTURE
from musif.extract.features.ambitus.constants import (HIGHEST_NOTE_INDEX,
                                                      LOWEST_NOTE_INDEX)
from musif.extract.features.harmony.constants import (KEY_MODULATORY,
                                                      KEY_PERCENTAGE,
                                                      KEY_PREFIX)
from musif.extract.features.interval.constants import TRIMMED_INTERVALLIC_MEAN
from musif.extract.features.prefix import get_part_prefix, get_sound_prefix
from musif.extract.features.scale.constants import DEGREE_PREFIX
from musif.extract.features.scoring.constants import (FAMILY_INSTRUMENTATION,
                                                      FAMILY_SCORING, VOICES)
from musif.logs import pinfo
from pandas import DataFrame
from tqdm import tqdm

from .constants import voices_list_prefixes


def replace_nans(df):
    for col in df.columns:
            if 'Interval' in col or col.startswith('Key_') or col.startswith((CHORD_prefix,'Chords_','Additions_','Numerals_')) or col.endswith(('_DottedRhythm','_DoubleDottedRhythm'))  or ('_Degree' and TRIMMED_INTERVALLIC_MEAN and '_Dyn') in col:
                df[col]= df[col].fillna('NA')
            

def merge_duetos_trios(df: DataFrame)-> None:
    generic_sound_voice_prefix = get_sound_prefix('Voice')
    
    df = df[df[VOICES].notna()]
    multiple_voices = df[df[VOICES].str.contains(',')]
    pinfo(f'{multiple_voices.shape[0]} arias were found with duetos/trietos. Calculating averages.')
    voice_cols = [col for col in df.columns.values if any(voice in col for voice in voices_list_prefixes)]
    
    
    for index in tqdm(multiple_voices.index):
        name = df.at[index, FILE_NAME]
        pinfo(f'\nMerging dueto/trieto {name}')
        all_voices = df.at[index, VOICES].split(',')

        first_voice = all_voices[0]
        columns_to_merge = [i for i in voice_cols if first_voice in i.lower()]
        for col in columns_to_merge:
            similar_cols = []
            formatted_col = col.replace(get_part_prefix(first_voice), generic_sound_voice_prefix)
            for j in range(0, len(all_voices)):
                similar_col = col.replace(get_part_prefix(first_voice), get_part_prefix(all_voices[j]))
                if similar_col in df:
                    similar_cols.append(similar_col)
            if all(isinstance(x,str) or np.isnan(x) for x in df.loc[index,similar_cols]):
                df.drop(similar_cols, inplace = True, axis=1)
            elif HIGHEST_NOTE_INDEX in col or ('Largest' and 'Asc') in col:
                df.at[index,formatted_col] = df.loc[index, similar_cols].max()
                
            elif LOWEST_NOTE_INDEX in col or ('Largest' and 'Desc') in col:
                df.at[index,formatted_col] = df.loc[index, similar_cols].min()
                
            else:
                df.at[index,formatted_col] = df.loc[index, similar_cols].mean()
                
    return df

def merge_single_voices(df: DataFrame) -> None:
    generic_sound_voice_prefix = get_sound_prefix('Voice')
    pinfo('\nJoining voice parts...')
    singer_columns = [i for i in df.columns.values if any(voice in i for voice in voices_list_prefixes)]
    for col in singer_columns:
        singer_part=col.split('_')[0]
        generic_col="_".join(col.split('_')[1:])
        formatted_col = col.replace(singer_part+'_', generic_sound_voice_prefix)
        if formatted_col in df:
            continue
        columns_to_merge = [i for i in singer_columns if "_".join(i.split('_')[1:])==generic_col]
        for colum in columns_to_merge:
            df[colum].fillna(0)
        df[formatted_col] = df[columns_to_merge].sum(axis=1)

                
def join_part_degrees(total_degrees: List[str], part: str, df: DataFrame, sufix: str= '') -> None:
    part_degrees = [i for i in total_degrees if part in i]

    aug = [i for i in part_degrees if '#' in i]
    desc = [i for i in part_degrees if 'b' in i and not 'bb' in i]
    d_desc = [i for i in part_degrees if 'bb' in i]
    d_asc = [i for i in part_degrees if 'x' in i]

    pattern = '^'+part+'Degree'+'[0-9].*'
    degree_nat = [x for x in part_degrees if re.search(pattern, x)]
    degree_nonat = [i for i in part_degrees if i not in degree_nat]

    df[part+DEGREE_PREFIX+'_Asc'+sufix] = df[aug].sum(axis=1)
    df[part+DEGREE_PREFIX+'_Desc'+sufix] = df[desc].sum(axis=1)
    df[part+DEGREE_PREFIX+'_Dasc'+sufix] = df[d_asc].sum(axis=1)
    df[part+DEGREE_PREFIX+'_Ddesc'+sufix] = df[d_desc].sum(axis=1)
    df[part+DEGREE_PREFIX+'_Nat'+sufix] = df[degree_nat].sum(axis=1)
    df[part+DEGREE_PREFIX+'_Nonat'+sufix] = df[degree_nonat].sum(axis=1)

def log_errors_and_shape(composer_counter: list, novoices_counter: list, df: DataFrame) -> None:
    pinfo(f"\nTotal files skipped by composer: {len(composer_counter)}")
    pinfo(str(composer_counter))
    pinfo(f"\nTotal files skipped by no-voices: { len(novoices_counter)}")
    pinfo(str(novoices_counter))
    # pinfo(f"\nTotal files skipped by duetos/trietos: {len(duetos_counter)}")
    # pinfo(str(duetos_counter))
    pinfo(f"\nFinal shape of the DataFrame: {df.shape[0]} scores, {df.shape[1]} features")

def delete_columns(data: DataFrame, config: dictConfig) -> None:
        pinfo('\nDeleting not useful columns...')
        for inst in config[INSTRUMENTS_TO_DELETE]:
            data.drop([i for i in data.columns if 'Part'+inst in i], axis = 1, inplace=True)
            
        for substring in config[SUBSTRING_TO_DELETE]:
            data.drop([i for i in data.columns if substring in i], axis = 1, inplace=True)
            
        data.drop([i for i in data.columns if i.endswith(tuple(config[ENDSWITH]))], axis = 1, inplace=True)
        data.drop([i for i in data.columns if i.startswith(tuple(config[STARTSWITH]))], axis = 1, inplace=True)
        data.drop([col for col in data.columns if any(substring in col for substring in tuple(config['columns_contain']))], axis = 1, inplace=True)
       
        presence = ['Presence_of_'+str(i) for i in config['delete_presence']]
        if all(item in data.columns for item in presence):
            data.drop(presence, axis = 1, inplace=True,  errors='ignore')
        
        # Sound features 
        data.drop([i for i in data.columns if i.startswith('Sound') and not 'Voice' in i], axis = 1, inplace=True)
        
        delete_exceptions(data)

def delete_exceptions(data) -> None:
    # Delete Vn when it is alone
    data.drop(data.columns[data.columns.str.contains(get_part_prefix('Vn'))], axis = 1, inplace=True)
    if 'PartVnI__PartVoice__'+TEXTURE in data:
        del data['PartVnI__PartVoice__Texture']

    if (FAMILY_INSTRUMENTATION and FAMILY_SCORING) in data:
        data.drop([FAMILY_INSTRUMENTATION, FAMILY_SCORING], axis = 1, inplace=True)

    # remove empty voices
    empty_voices = [col for col in data.columns if col.startswith(tuple(voices_list_prefixes)) and all(data[col].isnull().values)]
    if empty_voices:
        data.drop(empty_voices, axis = 1, inplace=True)

def split_passion_A(data: DataFrame) -> None:
    data['Label_PassionA_primary']=data['Label_PassionA'].str.split(';', expand=True)[0]
    data['Label_PassionA_secundary']=data['Label_PassionA'].str.split(';', expand=True)[1]
    data['Label_PassionA_secundary'].fillna(data['Label_PassionA_primary'], inplace=True)
    data.drop('Label_PassionA', axis = 1, inplace=True)
  
def join_keys(df: DataFrame) -> None:
        key_SD = [i for i in [KEY_PREFIX+'IV'+KEY_PERCENTAGE, KEY_PREFIX+'II'+KEY_PERCENTAGE, KEY_PREFIX+'VI'+KEY_PERCENTAGE] if i in df]
        key_sd =  [i for i in [KEY_PREFIX+'iv'+KEY_PERCENTAGE, KEY_PREFIX+'ii'+KEY_PERCENTAGE] if i in df]
        key_tonic =  [i for i in [KEY_PREFIX+'I'+KEY_PERCENTAGE, KEY_PREFIX+'i'+KEY_PERCENTAGE] if i in df]
        key_rel =  [i for i in [KEY_PREFIX+'III'+KEY_PERCENTAGE, KEY_PREFIX+'vi'+KEY_PERCENTAGE] if i in df]

        total_key=key_rel+key_tonic+key_sd+key_SD
        others_key=[i for i in df.columns if KEY_PREFIX in i and i not in total_key and KEY_MODULATORY not in i]

        df[KEY_PREFIX + 'SD' + KEY_PERCENTAGE]=df[key_SD].sum(axis=1)
        df[KEY_PREFIX+'sd'+KEY_PERCENTAGE]=df[key_sd].sum(axis=1)
        df[KEY_PREFIX+'SubD'+KEY_PERCENTAGE]=df[KEY_PREFIX+'sd'+KEY_PERCENTAGE] + df[KEY_PREFIX+'SD'+KEY_PERCENTAGE]
        df[KEY_PREFIX+'T'+KEY_PERCENTAGE] = df[key_tonic].sum(axis=1)
        df[KEY_PREFIX+'rel'+KEY_PERCENTAGE] = df[key_rel].sum(axis=1)
        df[KEY_PREFIX+'Other'+KEY_PERCENTAGE] = df[others_key].sum(axis=1)
        # df.drop(total_key+others_key, axis = 1, inplace=True)

def join_keys_modulatory(df: DataFrame):
        key_SD = [i for i in [KEY_PREFIX+KEY_MODULATORY+'IV',KEY_PREFIX+KEY_MODULATORY+'II', KEY_PREFIX+KEY_MODULATORY+'VI'] if i in df]
        key_sd = [i for i in [KEY_PREFIX+KEY_MODULATORY+'iv',KEY_PREFIX+KEY_MODULATORY+'ii'] if i in df]
        key_tonic = [i for i in [KEY_PREFIX+KEY_MODULATORY+'I',KEY_PREFIX+KEY_MODULATORY+'i'] if i in df]
        key_rel = [i for i in [KEY_PREFIX+KEY_MODULATORY+'III',KEY_PREFIX+KEY_MODULATORY+'vi'] if i in df]

        total_key_mod=key_rel+key_tonic+key_sd+key_SD
        others_key_mod=[i for i in df.columns if KEY_PREFIX+KEY_MODULATORY in i and i not in total_key_mod]

        df[KEY_PREFIX+KEY_MODULATORY+'SD']=df[key_SD].sum(axis=1)
        df[KEY_PREFIX+KEY_MODULATORY+'sd']=df[key_sd].sum(axis=1)
        df[KEY_PREFIX+KEY_MODULATORY+'SubD']=df[KEY_PREFIX+KEY_MODULATORY+'sd'] + df[KEY_PREFIX+KEY_MODULATORY+'SD']
        df[KEY_PREFIX+KEY_MODULATORY+'T'] = df[key_tonic].sum(axis=1)
        df[KEY_PREFIX+KEY_MODULATORY+'rel'] = df[key_rel].sum(axis=1)
        df[KEY_PREFIX+KEY_MODULATORY+'Other'] = df[others_key_mod].sum(axis=1)
        
def merge_dataframes(name: str, dest_path: str) -> None:
    csv='.csv'
    name1 = name+'_1'+csv
    name2 = name+'_2'+csv
    
    df2 = pd.read_csv(name2)
    df1 = pd.read_csv(name1)
    total_dataframe = pd.concat((df1, df2), axis=0)
    total_dataframe.to_csv(dest_path, index=False)
