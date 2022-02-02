from telnetlib import EL
import pandas as pd

# from musif import FeaturesExtractor
# from musif.extract.extract import FilesValidator
import sys

from tqdm import tqdm
sys.path.insert(0, "../musif")
sys.path.insert(0, "../musif/musif") 
from musif.extract.extract import FeaturesExtractor, FilesValidator

from musif.common.utils import read_dicts_from_csv
# from musif.extract.features.ambitus.constants import HIGHEST_NOTE_INDEX,  LOWEST_NOTE_INDEX
from musif.extract.features.composer.handler import COMPOSER
# from musif.extract.features.core.constants import NOTES_MEAN, SOUNDING_MEASURES_MEAN
from musif.extract.features.density.constants import DENSITY, SOUNDING_DENSITY
from musif.extract.features.file_name.constants import ARIA_ID, ARIA_LABEL
from musif.extract.features.interval.constants import ABSOLUTE_INTERVALLIC_KURTOSIS, ABSOLUTE_INTERVALLIC_MEAN, \
    ABSOLUTE_INTERVALLIC_SKEWNESS, ABSOLUTE_INTERVALLIC_STD, ABSOLUTE_INTERVALLIC_TRIM_DIFF, \
    ABSOLUTE_INTERVALLIC_TRIM_RATIO, ASCENDING_INTERVALS_PER, ASCENDING_SEMITONES_SUM, DESCENDING_INTERVALS_PER, \
    DESCENDING_SEMITONES_SUM, INTERVALLIC_KURTOSIS, INTERVALLIC_MEAN, INTERVALLIC_SKEWNESS, INTERVALLIC_STD, \
    INTERVALLIC_TRIM_DIFF, INTERVALLIC_TRIM_RATIO, INTERVALS_AUGMENTED_ALL_PER, INTERVALS_AUGMENTED_ASC_PER, \
    INTERVALS_AUGMENTED_DESC_PER, INTERVALS_BEYOND_OCTAVE_ALL_PER, INTERVALS_BEYOND_OCTAVE_ASC_PER, \
    INTERVALS_BEYOND_OCTAVE_DESC_PER, INTERVALS_DIMINISHED_ALL_PER, INTERVALS_DIMINISHED_ASC_PER, \
    INTERVALS_DIMINISHED_DESC_PER, INTERVALS_DOUBLE_AUGMENTED_ALL_PER, INTERVALS_DOUBLE_AUGMENTED_ASC_PER, \
    INTERVALS_DOUBLE_AUGMENTED_DESC_PER, INTERVALS_DOUBLE_DIMINISHED_ALL_PER, INTERVALS_DOUBLE_DIMINISHED_ASC_PER, \
    INTERVALS_DOUBLE_DIMINISHED_DESC_PER, INTERVALS_MAJOR_ALL_PER, INTERVALS_MAJOR_ASC_PER, INTERVALS_MAJOR_DESC_PER, \
    INTERVALS_MINOR_ALL_PER, INTERVALS_MINOR_ASC_PER, INTERVALS_MINOR_DESC_PER, INTERVALS_PERFECT_ALL_PER, \
    INTERVALS_PERFECT_ASC_PER, INTERVALS_PERFECT_DESC_PER, INTERVALS_WITHIN_OCTAVE_ALL_PER, \
    INTERVALS_WITHIN_OCTAVE_ASC_PER, INTERVALS_WITHIN_OCTAVE_DESC_PER, LARGEST_ABSOLUTE_SEMITONES_ALL, \
    LARGEST_ABSOLUTE_SEMITONES_ASC, LARGEST_ABSOLUTE_SEMITONES_DESC, LARGEST_SEMITONES_ALL, LARGEST_SEMITONES_ASC, \
    LARGEST_SEMITONES_DESC, LEAPS_ALL_PER, LEAPS_ASC_PER, LEAPS_DESC_PER, REPEATED_NOTES_PER, \
    SMALLEST_ABSOLUTE_SEMITONES_ALL, SMALLEST_ABSOLUTE_SEMITONES_ASC, SMALLEST_ABSOLUTE_SEMITONES_DESC, \
    SMALLEST_SEMITONES_ALL, SMALLEST_SEMITONES_ASC, SMALLEST_SEMITONES_DESC, STEPWISE_MOTION_ALL_PER, \
    STEPWISE_MOTION_ASC_PER, STEPWISE_MOTION_DESC_PER, TRIMMED_ABSOLUTE_INTERVALLIC_MEAN, \
    TRIMMED_ABSOLUTE_INTERVALLIC_STD, TRIMMED_INTERVALLIC_MEAN, TRIMMED_INTERVALLIC_STD
# from musif.extract.features.key.constants import KEY, KEY_SIGNATURE_TYPE, MODE
from musif.extract.features.lyrics.constants import SYLLABIC_RATIO, SYLLABLES
from musif.extract.features.prefix import get_part_prefix, get_sound_prefix
from musif.extract.features.scoring.constants import FAMILY_INSTRUMENTATION, INSTRUMENTATION, NUMBER_OF_PARTS, SCORING, \
    VOICES
from musif.extract.features.tempo.constants import NUMERIC_TEMPO, TEMPO, TEMPO_GROUPED_1, TEMPO_GROUPED_2, \
    TIME_SIGNATURE, \
    TIME_SIGNATURE_GROUPED
import numpy as np
import os

label_by_col = {
        "Basic_passion": "Label_BasicPassion",
        "PassionA": "Label_PassionA",
        "PassionB": "Label_PassionB",
        "Value": "Label_Value",
        "Value2": "Label_Value2",
        "Time": "Label_Time",
    }

def replace_nans(df):
    for col in df.columns:
        if '_Interval' in col or col.startswith('Key_') or col.startswith('Chord_') or col.startswith('Chords_') or col.startswith('Additions_'):
            df_analysis[col]= df_analysis[col].fillna(0)

if __name__ == "__main__":
    os.system("python scripts/metadata_updater.py")
    data_dir = r'../Corpus_200/xml'
    musescore_dir = r'../Corpus_200/musescore'

    check_file = 'parsed_files.csv'
    name = "features_200"

    df = FeaturesExtractor("scripts/config_drive.yml", data_dir=data_dir, musescore_dir=musescore_dir, check_file=None).extract()
    # df = FeaturesExtractor("scripts/config_drive.yml", check_file=None).extract()

    df.to_csv(name+"_extraction.csv", index=False)
    
    # df = pd.read_csv(name+"_extraction.csv", low_memory=False, sep=',', encoding_errors='replace')
    df['FileName'].to_csv(check_file)

    passions = read_dicts_from_csv("scripts/Passions.csv")

    data_by_aria_label = {label_data["Label"]: label_data for label_data in passions}

    data_list = []
    for col, label in label_by_col.items():
        values = []
        for index, row in df.iterrows():
            data_by_aria = data_by_aria_label.get(row["AriaLabel"])
            label_value = data_by_aria[col] if data_by_aria else None
            values.append(label_value)
        df[label] = values
    
    #pre-process data
    del df['Label_Passions']
    del df['Label_Sentiment']

    df = df[~df["Label_BasicPassion"].isnull()]
    df.replace(0.0, np.nan, inplace=True)
    df.dropna(axis=1, how='all', inplace=True)
    
    composer_counter = []
    novoices_counter = []
    duetos_counter = []

    cols = df.columns.tolist()
    for index, row in df.iterrows():
        if pd.isnull(row[COMPOSER]):
            print(row["Composer"])
            print(row["FileName"])
            composer_counter.append(row["FileName"])
            continue
        voice = row[VOICES]

        if pd.isnull(voice):
            print(row["FileName"])
            novoices_counter.append(row["FileName"])
            continue

        if "," in voice:
            duetos_counter.append(row["FileName"])
            continue
        voice_prefix = get_part_prefix(voice)

        generic_sound_voice_prefix = get_sound_prefix('Voice')


        data_item = {}
        for col in cols:
                formatted_col = col.replace(voice_prefix, generic_sound_voice_prefix)
    
                data_item[formatted_col] = row[col]

        data_list.append(data_item)
    
    df_analysis = pd.DataFrame(data_list)
    voices_list =  ['sop','ten','alt','bar','bbar']
    voices_list=['Part' + i.capitalize() for i in voices_list]
    
    for col in tqdm(df_analysis.columns.to_list()):
                if 'HighestNote' in col or 'LowestNote' in col:
                    del df_analysis[col]
                    print('Removed highest/lowest note:', col)

                elif 'PartOb' in col :
                    print('Removed Ob: ', col)
                    del df_analysis[col]
                    continue

                elif 'VnII' in col :
                    print('Removed VnII: ', col)
                    del df_analysis[col]
                    continue
                
                elif 'PartVn_' in col :
                    print('Removed Vn: ', col)
                    del df_analysis[col]
                    continue

                elif 'Vc' in col :
                    print('Removed Vnc: ', col)
                    del df_analysis[col]
                    continue
                
                elif 'Cl' in col :
                    print('Removed Cl: ', col)
                    del df_analysis[col]
                    continue

                elif 'PartVa' in col :
                    print('Removed Va: ', col)
                    del df_analysis[col]
                    continue

                elif 'Tpt' in col :
                    print('Removed Tpt: ', col)
                    del df_analysis[col]
                    continue

                elif 'Hn' in col :
                    print('Removed Hn: ', col)
                    del df_analysis[col]
                    continue
                
                elif 'Fl' in col :
                    print('Removed Fl: ', col)
                    del df_analysis[col]
                    continue

                elif '_Count' in col:
                    print('Removed Count: ', col)
                    del df_analysis[col]
                    continue

                elif 'Sound' in col and not 'Voice' in col:
                    print('Removed Sound: ', col)
                    del df_analysis[col]
                    continue

                elif col.endswith(('_Notes', '_SoundingMeasures', '_Syllables')):
                    print('Removed Absolutes: ', col)
                    del df_analysis[col]
                    continue

                else:
                    if col.startswith(tuple(voices_list)):
                        if all(df_analysis[col].isnull().values):
                            print('Removed no-voice: ', col)
                            del df_analysis[col]
                            
    df_analysis.sort_values("AriaId", inplace=True)
    
    replace_nans(df_analysis)

    print("\nTotal files skipped by composer: ", len(composer_counter))
    print(composer_counter)
    print("\nTotal files skipped by no-voices: ", len(novoices_counter))

    print(novoices_counter)
    print("\nTotal files skipped by duetos/trietos: ", len(duetos_counter))
    print(duetos_counter)

    df_analysis = df_analysis.reindex(sorted(df_analysis.columns), axis=1)
    df_analysis.to_csv(name + ".csv", index=False)
    print(df_analysis.shape)

