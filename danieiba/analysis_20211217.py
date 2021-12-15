import pandas as pd

from musif import FeaturesExtractor
from musif.common.utils import read_dicts_from_csv
from musif.extract.features.ambitus.constants import HIGHEST_NOTE_INDEX, LOWEST_NOTE_INDEX
from musif.extract.features.composer.handler import COMPOSER
from musif.extract.features.core.constants import NOTES_MEAN, SOUNDING_MEASURES_MEAN
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
from musif.extract.features.key.constants import KEY, KEY_SIGNATURE_TYPE, MODE
from musif.extract.features.lyrics.constants import SYLLABIC_RATIO, SYLLABLES
from musif.extract.features.prefix import get_part_prefix
from musif.extract.features.scoring.constants import FAMILY_INSTRUMENTATION, INSTRUMENTATION, NUMBER_OF_PARTS, SCORING, \
    VOICES
from musif.extract.features.tempo.constants import NUMERIC_TEMPO, TEMPO, TEMPO_GROUPED_1, TEMPO_GROUPED_2, \
    TIME_SIGNATURE, \
    TIME_SIGNATURE_GROUPED

if __name__ == "__main__":

    df = FeaturesExtractor("config.yml").extract()
    df.to_csv("myfeatures.csv", index=False)
    df = pd.read_csv("myfeatures.csv", low_memory=False)
    cols = df.columns.tolist()
    passions = read_dicts_from_csv("passions2.csv")
    data_by_aria_label = {label_data["Label"]: label_data for label_data in passions}
    label_by_col = {
        "Basic_passion": "Label_BasicPassion",
        "PassionA": "Label_PassionA",
        "PassionB": "Label_PassionB",
        "Value": "Label_Value",
        "Value2": "Label_Value2",
        "Time": "Label_Time",
    }
    for col, label in label_by_col.items():
        values = []
        for index, row in df.iterrows():
            data_by_aria = data_by_aria_label.get(row["AriaLabel"])
            label_value = data_by_aria[col] if data_by_aria else None
            values.append(label_value)
        df[label] = values
    df = df[~df["Label_BasicPassion"].isnull()]
    data_list = []
    for index, row in df.iterrows():
        if pd.isnull(row[COMPOSER]):
            continue
        voice = row[VOICES]
        if pd.isnull(voice):
            print(row["FileName"])
            continue
        if "," in voice:
            continue
        voice_prefix = get_part_prefix(voice)
        generic_voice_prefix = get_part_prefix("Voice")
        data_item = {}
        for col in cols:
            formatted_col = col.replace(voice_prefix, generic_voice_prefix)
            data_item[formatted_col] = row[col]
        data_list.append(data_item)
    df_analysis = pd.DataFrame(data_list)
    df_analysis.sort_values("AriaId", inplace=True)
    df_analysis.to_csv("analysis_20211217.csv", index=False)
    print(df_analysis.shape)
