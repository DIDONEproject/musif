import sys
from time import process_time_ns

import pandas as pd

from musif.logs import pdebug

sys.path.insert(0, "../musif")
import os
import re

import numpy as np
from musif.common.sort import sort_columns
from musif.common.utils import read_dicts_from_csv
from musif.extract.extract import FeaturesExtractor, FilesValidator
from musif.extract.features.composer.handler import COMPOSER
from musif.extract.features.file_name.constants import ARIA_ID, ARIA_LABEL
from musif.extract.features.harmony.constants import (KEY_MODULATORY,
                                                      KEY_PERCENTAGE,
                                                      CHORDS_GROUPING_prefix,
                                                      KEY_prefix)
from musif.extract.features.interval.constants import TRIMMED_INTERVALLIC_MEAN
from musif.extract.features.scale.constants import DEGREE_PREFIX
from musif.extract.features.core.constants import FILE_NAME
from musif.extract.features.prefix import get_part_prefix, get_sound_prefix
from musif.extract.features.scoring.constants import (FAMILY_INSTRUMENTATION, FAMILY_SCORING, INSTRUMENTATION,
                                                      NUMBER_OF_PARTS, SCORING,
                                                      VOICES)
from musif.extract.features.tempo.constants import NUMBER_OF_BEATS
columns_order= [ARIA_ID, 'FileName', 'AriaOpera', ARIA_LABEL, 'AriaName','Act', 'Scene', 'ActAndScene', 'Year', 'Decade', 'Composer', 'City', 'Territory', 'Character', 'Role', 'Gender', 'Form', 'Key', 'KeySignature', 'KeySignatureType', INSTRUMENTATION, SCORING, 'RoleType', 'Voices']

PRESENCE='Presence_of'

label_by_col = {
        "Basic_passion": "Label_BasicPassion",
        "PassionA": "Label_PassionA",
        "PassionB": "Label_PassionB",
        "Value": "Label_Value",
        "Value2": "Label_Value2",
        "Time": "Label_Time",
    }

parts_to_keep=['vnI', 'bs']
wipe_instruments=['VnII', 'Vc', 'Cl', 'Tpt', 'Hn', 'Fl', 'VnIV']
instruments_to_kill=['Ob', 'Cor', 'Bn', 'Va']

voices_list = ['Part' + i.capitalize() for i in ['sop','ten','alt','bar','bbar', 'bass']]
    
def replace_nans(df_analysis):
    for col in df_analysis.columns:
        if '_Interval' in col or col.startswith('Key_') or col.startswith('Chord_') or col.startswith('Chords_') or col.startswith('Additions_') or col.startswith('Numerals_') or col.endswith('_DottedRhythm') or col.endswith('_DoubleDottedRhythm')  or '_Degree' in col or TRIMMED_INTERVALLIC_MEAN in col or PRESENCE in col:
            df_analysis[col]= df_analysis[col].fillna(0)

def delete_not_useful_columns(df):
    #Delete unwanted instruments
    for inst in instruments_to_kill:
        df.drop([i for i in df.columns if 'Part'+inst in i], axis = 1, inplace=True)
    
    for inst in wipe_instruments:
        df.drop([i for i in df.columns if inst in i], axis = 1, inplace=True)

    df.drop([i for i in df.columns if get_part_prefix('Vn') in i], axis = 1, inplace=True)

    # Delete other unuseful columns
    df.drop([i for i in df.columns if i.startswith('HighestNote') or i.startswith('LowestNote')], axis = 1, inplace=True)
    df.drop([i for i in df.columns if '_Count' in i], axis = 1, inplace=True)
    df.drop([i for i in df.columns if i.startswith('SoundVoice_Dyn')], axis = 1, inplace=True)
    df.drop([i for i in df.columns if i.startswith(('FamilyWw', 'FamilyBr', 'EndOfThemeA', NUMBER_OF_BEATS))], axis = 1, inplace=True)
    df.drop([i for i in df.columns if i.endswith(('_Notes', '_SoundingMeasures', '_Syllables', '_NumberOfFilteredParts', NUMBER_OF_PARTS, '_NotesMean', 'Librettist', '_LargestIntervalAsc', '_LargestIntervalAll','_LargestIntervalDesc', '_NotesMean', 'Semitones_Sum', '_MeanInterval'))], axis = 1, inplace=True)
    df.drop([i for i in df.columns if i.endswith(('_HighestNote', '_LowestNote'))], axis = 1, inplace=True)
    df.drop([FAMILY_INSTRUMENTATION, FAMILY_SCORING], axis = 1, inplace=True)

    cols_to_remove=('_SoundingMeasuresMean', '_SmallestSemitones', '_SmallestAbsolute', '_SmallestInterval')
    df.drop([col for col in df.columns if any(substring in col for substring in cols_to_remove)], axis = 1, inplace=True)
    
    cols_to_remove=['Presence_of_bs', 'Presence_of_va', 'Presence_of_vc', 'Presence_of_vn']
    df.drop(cols_to_remove, axis = 1, inplace=True)
    
    df.drop([i for i in df.columns if 'Sound' in i and not 'Voice' in i], axis = 1, inplace=True)
    if 'PartVnI__PartVoice__Texture' in df:
        del df['PartVnI__PartVoice__Texture']
    #remove empty voices
    df.drop([col for col in df.columns if col.startswith(tuple(voices_list)) and all(df[col].isnull().values)], axis = 1, inplace=True)

def delete_previous_items(df):
    errors=pd.read_csv('errors.csv', low_memory=False, sep='\n', encoding_errors='replace',header=0)['FileName'].tolist()
    for item in errors:
        index = df.index[df['FileName']==item]
        df.drop(index, axis=0, inplace=True)

def assign_labels(label_by_col, df, split_passionA):
    passions = read_dicts_from_csv("scripts/Passions.csv")
    data_by_aria_label = {label_data["Label"]: label_data for label_data in passions}
    for col, label in label_by_col.items():
        values = []
        for index, row in df.iterrows():
            data_by_aria = data_by_aria_label.get(row["AriaLabel"])
            label_value = data_by_aria[col] if data_by_aria else None
            values.append(label_value)
        df[label] = values
    if split_passionA:
        df['Label_PassionA_primary']=df['Label_PassionA'].str.split(';', expand=True)[0]
        df['Label_PassionA_secundary']=df['Label_PassionA'].str.split(';', expand=True)[1]
        df['Label_PassionA_secundary'].fillna(df['Label_PassionA_primary'], inplace=True)
        df.drop('Label_PassionA', axis = 1, inplace=True)

def preprocess_data(df):
    if 'Label_Passions' in df:
        del df['Label_Passions']

    if 'Label_Sentiment' in df:
        del df['Label_Sentiment']

    df = df[~df["Label_BasicPassion"].isnull()]
    df.replace(0.0, np.nan, inplace=True)
    df.dropna(axis=1, how='all', inplace=True)
    df.reset_index(inplace=True)

def scan_and_purge_df2(df):
    composer_counter = []
    novoices_counter = []
    duetos_counter = []
    for i, comp in enumerate(df[COMPOSER].values):
        if pd.isnull(comp):
            composer_counter.append(df[FILE_NAME][i])
            df.drop(i, axis = 0, inplace=True)
            

    for i, voice in enumerate(df[VOICES].values):
        if pd.isnull(voice):
            novoices_counter.append(df[FILE_NAME][i])
            df.drop(i, axis = 0, inplace=True)

        if ',' in voice:
            duetos_counter.append(df[FILE_NAME][i])
            df.drop(i, axis = 0, inplace=True)

    merge_voices2(df)

    return composer_counter,novoices_counter,duetos_counter

def scan_and_purge_df(df):
    composer_counter = []
    novoices_counter = []
    duetos_counter = []
    data_list = []
    cols = df.columns.tolist()

    for idx, row in df.iterrows():
        voice = row[VOICES]
        if pd.isnull(row[COMPOSER]):
            composer_counter.append(row["FileName"])
            continue

        if pd.isnull(voice):
            print(row["FileName"])
            novoices_counter.append(row["FileName"])
            continue

        if "," in voice:
            duetos_counter.append(row["FileName"])
            continue
        data_item = merge_voices(cols, row, voice)
        data_list.append(data_item)

    return composer_counter,novoices_counter,duetos_counter, data_list

def merge_voices(cols, row, voice):
    voice_prefix = get_part_prefix(voice)
    generic_sound_voice_prefix = get_sound_prefix('Voice')
    data_item = {}
    for col in cols:
            formatted_col = col.replace(voice_prefix, generic_sound_voice_prefix)
            data_item[formatted_col] = row[col]
    return data_item

def merge_voices2(df):
    generic_sound_voice_prefix=get_sound_prefix('Voice')
    for i, voice in enumerate(voices_list):
        voice_prefix = voice+'_'
        for j, col in enumerate(df.columns.values):
            if voice_prefix in col:
                formatted_col = col.replace(voice_prefix, generic_sound_voice_prefix)
                if formatted_col in df:
                    df[formatted_col].fillna(df[col], inplace=True)
                else:
                    df[formatted_col]=df[col]
                df.drop(col, axis=1, inplace=True)

def log_errors_and_shape(composer_counter, novoices_counter, duetos_counter, df_analysis):
    print("\nTotal files skipped by composer: ", len(composer_counter))
    print(composer_counter)
    print("\nTotal files skipped by no-voices: ", len(novoices_counter))
    print(novoices_counter)
    print("\nTotal files skipped by duetos/trietos: ", len(duetos_counter))
    print(duetos_counter)
    print("\nFinal shape of the DataFrame: ", df_analysis.shape)

def disgrate_instrumentation(df):
    for i, row in enumerate(df[INSTRUMENTATION]):
        for element in row.split(','):
            df.at[i, PRESENCE+'_'+element] = 1

def final_process_data(columns_order, name, composer_counter, novoices_counter, duetos_counter, df_analysis):
    df_analysis.sort_values(ARIA_ID, inplace=True)
    replace_nans(df_analysis)
    log_errors_and_shape(composer_counter, novoices_counter, duetos_counter, df_analysis)
    df_analysis = df_analysis.reindex(sorted(df_analysis.columns), axis=1)
    df_analysis = sort_columns(df_analysis, columns_order)
    df_analysis.to_csv(name + ".csv", index=False)
    print('Data saved as {}'.format(str(name + ".csv")))
def group_keys_modulatory(df):

    df.update(df[[i for i in df.columns if KEY_prefix+KEY_MODULATORY in i]].fillna(0))
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

def group_keys(df):
    df.update(df[[i for i in df.columns if KEY_prefix in i]].fillna(0))
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

def join_degrees(total_degrees, part, df):

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

def iterate_degrees(parts_to_keep , join_degrees, df):
    total_degrees = [i for i in df.columns if '_Degree' in i]
    for part in parts_to_keep:
        join_degrees(total_degrees, get_part_prefix(part), df)

    join_degrees(total_degrees, get_sound_prefix('voice'), df)
    # df.drop(total_degrees, axis = 1, inplace=True)

if __name__ == "__main__":
    print('\nUpdating metadata files...')
    os.system("python scripts/metadata_updater.py")
    data_dir = r'../../_Ana\Music Analysis/xml/corpus_github/xml'
    # data_dir = r'../Half_Corpus/xml'
    musescore_dir = r'../../_Ana\Music Analysis/xml/corpus_github/musescore'
    
    grouped_analysis=True
    split_passionA=True
    delete=False
    check_file = 'parsed_files_new.csv'
    # check_file=None
    name = "features_new_total"
    
    # df = FeaturesExtractor("scripts/config_drive.yml", data_dir=data_dir, musescore_dir=musescore_dir, check_file=check_file).extract()
    # df.to_csv(name+"_extraction.csv", index=False)

    df = pd.read_csv(name+"_extraction.csv", low_memory=False, sep=',', encoding_errors='replace')
    # df['FileName'].to_csv(check_file, index=False)

    if delete:
        delete_previous_items(df)
    
    assign_labels(label_by_col, df, split_passionA)
    import timeit

    print('\nPreprocessing data...')
    preprocess_data(df)

    start = timeit.timeit()
    disgrate_instrumentation(df)
    end = timeit.timeit()
    print('Elapsed Disgregating: ', (end - start))

    print('\nScan and purge df ...')
    # from copy import deepcopy
    # df1=deepcopy(df)
    # df2=deepcopy(df)
    # start = timeit.timeit()
    # composer_counter, novoices_counter, duetos_counter, data_list = scan_and_purge_df(df1)
    # end = timeit.timeit()
    # print('Elapsed time purging: ', (end - start))
    start = timeit.timeit()
    composer_counter, novoices_counter, duetos_counter = scan_and_purge_df2(df)
    end = timeit.timeit()
    print('Elapsed time purging2: ',(end - start))

    # df = pd.DataFrame(data_list)
    start = timeit.timeit()
    print('Deleiting not useful columns...')
    delete_not_useful_columns(df)
    end = timeit.timeit()
    print('Elapsed time deleiting columns: ', (end - start))

    if grouped_analysis:
        df.drop([i for i in df.columns if 'Degree' in i and not '_relative' in i], axis = 1, inplace=True)
        df.drop([i for i in df.columns if i.startswith(CHORDS_GROUPING_prefix+'1')], axis = 1, inplace=True)

        group_keys_modulatory(df)
        group_keys(df)
        iterate_degrees(parts_to_keep, join_degrees, df)

    final_process_data(columns_order, name, composer_counter, novoices_counter, duetos_counter, df)


