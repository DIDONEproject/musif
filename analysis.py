import pandas as pd
import numpy as np

from musif.extract.features.ambitus import HIGHEST_INDEX, LOWEST_INDEX
from musif.extract.features.custom.file_name import ARIA_DECADE, ARIA_YEAR
from musif.extract.features.density import DENSITY, MEASURES, MEASURES_MEAN, SOUNDING_DENSITY
from musif.extract.features.interval import ABSOLUTE_INTERVALLIC_MEAN, ABSOLUTE_INTERVALLIC_STD, \
    ABSOLUTE_INTERVALS_KURTOSIS, \
    ABSOLUTE_INTERVALS_SKEWNESS, INTERVALLIC_MEAN, \
    INTERVALLIC_STD, \
    INTERVALS_AUGMENTED_ALL_PER, INTERVALS_DIMINISHED_ALL_PER, INTERVALS_DOUBLE_AUGMENTED_ALL_PER, \
    INTERVALS_DOUBLE_DIMINISHED_ALL_PER, INTERVALS_KURTOSIS, \
    INTERVALS_MAJOR_ALL_PER, \
    INTERVALS_MINOR_ALL_PER, \
    INTERVALS_PERFECT_ALL_PER, INTERVALS_SKEWNESS, LEAPS_ALL_PER, REPEATED_NOTES_PER, STEPWISE_MOTION_ALL_PER
from musif.extract.features.key import KEY, KEY_SIGNATURE_TYPE, MODE
from musif.extract.features.lyrics import SYLLABIC_RATIO
from musif.extract.features.prefix import get_part_prefix
from musif.extract.features.scoring import FAMILY_INSTRUMENTATION, INSTRUMENTATION, NUMBER_OF_PARTS, VOICES
from musif.extract.features.tempo import TEMPO, TEMPO_GROUPED_1, TEMPO_GROUPED_2, TIME_SIGNATURE, TIME_SIGNATURE_GROUPED

if __name__ == "__main__":

    df = pd.read_csv("myfeatures.csv", low_memory=False)
    df = df[~df["Label_Sentiment"].isnull()]
    df = df[df["FamilyVoice_NumberOfParts"] == 1]
    data_list = []
    for index, row in df.iterrows():
        voice = row[VOICES]
        input_parts = [voice, "vnI", "vnII", "va", "bs"]
        output_parts = ["Voice", "vnI", "vnII", "va", "bs"]
        input_parts_prefixes = [get_part_prefix(part_prefix) for part_prefix in input_parts]
        output_parts_prefixes = [get_part_prefix(part_prefix) for part_prefix in output_parts]
        data_item = {
            "Mode": row[MODE],
            "Key": row[KEY],
            "KeySignatureType": row[KEY_SIGNATURE_TYPE],
            "NumberOfParts": row[NUMBER_OF_PARTS],
            "FamilyInstrumentation": row[FAMILY_INSTRUMENTATION],
            "Instrumentation": row[INSTRUMENTATION],
            "Tempo": row[TEMPO],
            "TempoGrouped1": row[TEMPO_GROUPED_1],
            "TempoGrouped2": row[TEMPO_GROUPED_2],
            "TimeSignature": row[TIME_SIGNATURE],
            "TimeSignatureGrouped": row[TIME_SIGNATURE_GROUPED],
            "Year": row[ARIA_YEAR],
            "Decade": row[ARIA_DECADE],
            f"{get_part_prefix('Voice')}SyllabicRatio": row[f"{get_part_prefix(voice)}{SYLLABIC_RATIO}"],
            "Score_Density": row[f"Score_{DENSITY}"],
            "Score_SoundingDensity": row[f"Score_{SOUNDING_DENSITY}"],
            "Score_Measures": row[f"Score_{MEASURES}"],
            "Score_MeasuresMean": row[f"Score_{MEASURES_MEAN}"],
            "Label_Sentiment": row["Label_Sentiment"],
            "Label_BasicPassion": row["Label_BasicPassion"],
            "Label_Passions": row["Label_Passions"],
            "Label_Time": row["Label_Time"],
        }
        for input_part, output_part in zip(input_parts_prefixes, output_parts_prefixes):
            data_item[f"{output_part}HighestNoteIndex"] = row[f"{input_part}{HIGHEST_INDEX}"]
            data_item[f"{output_part}LowestNoteIndex"] = row[f"{input_part}{LOWEST_INDEX}"]
            data_item[f"{output_part}Density"] = row[f"{input_part}{DENSITY}"]
            data_item[f"{output_part}SoundingDensity"] = row[f"{input_part}{SOUNDING_DENSITY}"]
            data_item[f"{output_part}IntervallicMean"] = row[f"{input_part}{INTERVALLIC_MEAN}"]
            data_item[f"{output_part}IntervallicStd"] = row[f"{input_part}{INTERVALLIC_STD}"]
            data_item[f"{output_part}IntervallicSkewness"] = row[f"{input_part}{INTERVALS_SKEWNESS}"]
            data_item[f"{output_part}IntervallicKurtosis"] = row[f"{input_part}{INTERVALS_KURTOSIS}"]
            data_item[f"{output_part}AbsoluteIntervallicMean"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_MEAN}"]
            data_item[f"{output_part}AbsoluteIntervallicStd"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_STD}"]
            data_item[f"{output_part}AbsoluteIntervallicSkewness"] = row[f"{input_part}{ABSOLUTE_INTERVALS_SKEWNESS}"]
            data_item[f"{output_part}AbsoluteIntervallicKurtosis"] = row[f"{input_part}{ABSOLUTE_INTERVALS_KURTOSIS}"]
            data_item[f"{output_part}IntervalsDiminishedAll"] = row[f"{input_part}{INTERVALS_DIMINISHED_ALL_PER}"]
            data_item[f"{output_part}IntervalsMinorAll"] = row[f"{input_part}{INTERVALS_MINOR_ALL_PER}"]
            data_item[f"{output_part}IntervalsPerfectAll"] = row[f"{input_part}{INTERVALS_PERFECT_ALL_PER}"]
            data_item[f"{output_part}IntervalsMajorAll"] = row[f"{input_part}{INTERVALS_MAJOR_ALL_PER}"]
            data_item[f"{output_part}IntervalsAugmentedAll"] = row[f"{input_part}{INTERVALS_AUGMENTED_ALL_PER}"]
            data_item[f"{output_part}LeapsAll"] = row[f"{input_part}{LEAPS_ALL_PER}"]
            data_item[f"{output_part}StepwiseMotionAll"] = row[f"{input_part}{STEPWISE_MOTION_ALL_PER}"]
            data_item[f"{output_part}RepeatedNotes"] = row[f"{input_part}{REPEATED_NOTES_PER}"]
        data_list.append(data_item)
    df_analysis = pd.DataFrame(data_list)
    df_analysis.to_csv("analysis.csv", index=False)
    print()
