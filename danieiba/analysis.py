import pandas as pd

from musif.common.utils import read_dicts_from_csv
from musif.extract.features.ambitus import HIGHEST_NOTE_INDEX, LOWEST_NOTE_INDEX
from musif.extract.features.composer import COMPOSER
from musif.extract.features.custom.file_name import ARIA_ID, ARIA_LABEL
from musif.extract.features.density import DENSITY, MEASURES_MEAN, NOTES_MEAN, SOUNDING_DENSITY, SOUNDING_MEASURES_MEAN
from musif.extract.features.interval import ABSOLUTE_INTERVALLIC_KURTOSIS, ABSOLUTE_INTERVALLIC_MEAN, \
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
from musif.extract.features.key import KEY, KEY_SIGNATURE_TYPE, MODE
from musif.extract.features.lyrics import SYLLABIC_RATIO, SYLLABLES
from musif.extract.features.prefix import get_part_prefix
from musif.extract.features.scoring import FAMILY_INSTRUMENTATION, INSTRUMENTATION, NUMBER_OF_PARTS, SCORING, VOICES
from musif.extract.features.tempo import NUMERIC_TEMPO, TEMPO, TEMPO_GROUPED_1, TEMPO_GROUPED_2, TIME_SIGNATURE, \
    TIME_SIGNATURE_GROUPED

if __name__ == "__main__":

    df = pd.read_csv("myfeatures.csv", low_memory=False)
    cols = df.columns.tolist()
    passions = read_dicts_from_csv("passions.csv")
    data_by_aria_label = {label_data["Label"]: label_data for label_data in passions}
    label_by_col = {
        "Basic_passion": "Label_BasicPassion",
        "Passion": "Label_Passions",
        "Value": "Label_Sentiment",
        "Time": "Label_Time",
    }
    for col, label in label_by_col.items():
        values = []
        for index, row in df.iterrows():
            data_by_aria = data_by_aria_label.get(row["AriaLabel"])
            label_value = data_by_aria[col] if data_by_aria else None
            values.append(label_value)
        df[label] = values
    df = df[~df["Label_Sentiment"].isnull()]
    data_list = []
    for index, row in df.iterrows():
        if pd.isnull(row[COMPOSER]):
            continue
        if not ("galuppi" in row[COMPOSER].lower() or "perez" in row[COMPOSER].lower()):
            continue
        voice = row[VOICES]
        if pd.isnull(voice):
            print(row["FileName"])
            continue
        if "," in voice:
            voice = voice.split(",")[0]
        input_parts = [voice, "vnI", "bs"]
        output_parts = ["Voice", "vnI", "bs"]
        input_parts_prefixes = [get_part_prefix(part_prefix) for part_prefix in input_parts]
        output_parts_prefixes = [get_part_prefix(part_prefix) for part_prefix in output_parts]
        data_item = {
            "AriaId": row[ARIA_ID],
            "Mode": row[MODE],
            "Key": row[KEY],
            "Composer": row[COMPOSER].split(" ")[-1].capitalize(),
            "KeySignatureType": row[KEY_SIGNATURE_TYPE],
            "NumberOfParts": row[NUMBER_OF_PARTS],
            "FamilyInstrumentation": row[FAMILY_INSTRUMENTATION],
            "Instrumentation": row[INSTRUMENTATION],
            "Tempo": row[TEMPO],
            "TempoNumeric": row[NUMERIC_TEMPO],
            "TempoGrouped1": row[TEMPO_GROUPED_1],
            "TempoGrouped2": row[TEMPO_GROUPED_2],
            "TimeSignature": row[TIME_SIGNATURE],
            "TimeSignatureGrouped": row[TIME_SIGNATURE_GROUPED],
            f"{get_part_prefix('Voice')}SyllabicRatio": row[f"{get_part_prefix(voice)}{SYLLABIC_RATIO}"],
            "Score_Density": row[f"Score_{DENSITY}"],
            "Score_SoundingDensity": row[f"Score_{SOUNDING_DENSITY}"],
            "Score_NotesMean": row[f"Score_{NOTES_MEAN}"],
            "Score_MeasuresMean": row[f"Score_{MEASURES_MEAN}"],
            "Score_SoundingMeasuresMean": row[f"Score_{SOUNDING_MEASURES_MEAN}"],
            "Label_TextId": row[ARIA_LABEL],
            "Label_Sentiment": row["Label_Sentiment"],
            "Label_BasicPassion": row["Label_BasicPassion"],
            "Label_Passions": row["Label_Passions"],
            "Label_Time": row["Label_Time"],
            "Score_IntervallicMean": row[f"Score_{INTERVALLIC_MEAN}"],
            "Score_IntervallicStd": row[f"Score_{INTERVALLIC_STD}"],
            "Score_IntervallicSkewness": row[f"Score_{INTERVALLIC_SKEWNESS}"],
            "Score_IntervallicKurtosis": row[f"Score_{INTERVALLIC_KURTOSIS}"],
            "Score_IntervallicTrimDiff": row[f"Score_{INTERVALLIC_TRIM_DIFF}"],
            "Score_IntervallicTrimRatio": row[f"Score_{INTERVALLIC_TRIM_RATIO}"],
            "Score_AbsoluteIntervallicMean": row[f"Score_{ABSOLUTE_INTERVALLIC_MEAN}"],
            "Score_AbsoluteIntervallicStd": row[f"Score_{ABSOLUTE_INTERVALLIC_STD}"],
            "Score_AbsoluteIntervallicSkewness": row[f"Score_{ABSOLUTE_INTERVALLIC_SKEWNESS}"],
            "Score_AbsoluteIntervallicKurtosis": row[f"Score_{ABSOLUTE_INTERVALLIC_KURTOSIS}"],
            "Score_AbsoluteIntervallicTrimDiff": row[f"Score_{ABSOLUTE_INTERVALLIC_TRIM_DIFF}"],
            "Score_AbsoluteIntervallicTrimRatio": row[f"Score_{ABSOLUTE_INTERVALLIC_TRIM_RATIO}"],
            "Score_AscendingIntervals": row[f"Score_{ASCENDING_INTERVALS_PER}"],
            "Score_AscendingSemitonesSum": row[f"Score_{ASCENDING_SEMITONES_SUM}"],
            "Score_DescendingIntervals": row[f"Score_{DESCENDING_INTERVALS_PER}"],
            "Score_DescendingSemitonesSum": row[f"Score_{DESCENDING_SEMITONES_SUM}"],
            "Score_IntervalsAugmentedAll": row[f"Score_{INTERVALS_AUGMENTED_ALL_PER}"],
            "Score_IntervalsAugmentedAsc": row[f"Score_{INTERVALS_AUGMENTED_ASC_PER}"],
            "Score_IntervalsAugmentedDesc": row[f"Score_{INTERVALS_AUGMENTED_DESC_PER}"],
            "Score_IntervalsBeyondOctaveAll": row[f"Score_{INTERVALS_BEYOND_OCTAVE_ALL_PER}"],
            "Score_IntervalsBeyondOctaveAsc": row[f"Score_{INTERVALS_BEYOND_OCTAVE_ASC_PER}"],
            "Score_IntervalsBeyondOctaveDesc": row[f"Score_{INTERVALS_BEYOND_OCTAVE_DESC_PER}"],
            "Score_IntervalsDiminishedAll": row[f"Score_{INTERVALS_DIMINISHED_ALL_PER}"],
            "Score_IntervalsDiminishedAsc": row[f"Score_{INTERVALS_DIMINISHED_ASC_PER}"],
            "Score_IntervalsDiminishedDesc": row[f"Score_{INTERVALS_DIMINISHED_DESC_PER}"],
            "Score_IntervalsDoubleAugmentedAll": row[f"Score_{INTERVALS_DOUBLE_AUGMENTED_ALL_PER}"],
            "Score_IntervalsDoubleAugmentedAsc": row[f"Score_{INTERVALS_DOUBLE_AUGMENTED_ASC_PER}"],
            "Score_IntervalsDoubleAugmentedDesc": row[f"Score_{INTERVALS_DOUBLE_AUGMENTED_DESC_PER}"],
            "Score_IntervalsDoubleDiminishedAll": row[f"Score_{INTERVALS_DOUBLE_DIMINISHED_ALL_PER}"],
            "Score_IntervalsDoubleDiminishedAsc": row[f"Score_{INTERVALS_DOUBLE_DIMINISHED_ASC_PER}"],
            "Score_IntervalsDoubleDiminishedDesc": row[f"Score_{INTERVALS_DOUBLE_DIMINISHED_DESC_PER}"],
            "Score_IntervalsMajorAll": row[f"Score_{INTERVALS_MAJOR_ALL_PER}"],
            "Score_IntervalsMajorAsc": row[f"Score_{INTERVALS_MAJOR_ASC_PER}"],
            "Score_IntervalsMajorDesc": row[f"Score_{INTERVALS_MAJOR_DESC_PER}"],
            "Score_IntervalsMinorAll": row[f"Score_{INTERVALS_MINOR_ALL_PER}"],
            "Score_IntervalsMinorAsc": row[f"Score_{INTERVALS_MINOR_ASC_PER}"],
            "Score_IntervalsMinorDesc": row[f"Score_{INTERVALS_MINOR_DESC_PER}"],
            "Score_IntervalsPerfectAll": row[f"Score_{INTERVALS_PERFECT_ALL_PER}"],
            "Score_IntervalsPerfectAsc": row[f"Score_{INTERVALS_PERFECT_ASC_PER}"],
            "Score_IntervalsPerfectDesc": row[f"Score_{INTERVALS_PERFECT_DESC_PER}"],
            "Score_IntervalsWithinOctaveAll": row[f"Score_{INTERVALS_WITHIN_OCTAVE_ALL_PER}"],
            "Score_IntervalsWithinOctaveAsc": row[f"Score_{INTERVALS_WITHIN_OCTAVE_ASC_PER}"],
            "Score_IntervalsWithinOctaveDesc": row[f"Score_{INTERVALS_WITHIN_OCTAVE_DESC_PER}"],
            "Score_LeapsAll": row[f"Score_{LEAPS_ALL_PER}"],
            "Score_LeapsAsc": row[f"Score_{LEAPS_ASC_PER}"],
            "Score_LeapsDesc": row[f"Score_{LEAPS_DESC_PER}"],
            "Score_RepeatedNotesPer": row[f"Score_{REPEATED_NOTES_PER}"],
            "Score_StepwiseMotionAll": row[f"Score_{STEPWISE_MOTION_ALL_PER}"],
            "Score_StepwiseMotionAsc": row[f"Score_{STEPWISE_MOTION_ASC_PER}"],
            "Score_StepwiseMotionDesc": row[f"Score_{STEPWISE_MOTION_DESC_PER}"],
            "Score_SyllabicRatio": row[f"Score_{SYLLABIC_RATIO}"],
            "Score_TrimmedAbsoluteIntervallicMean": row[f"Score_{TRIMMED_ABSOLUTE_INTERVALLIC_MEAN}"],
            "Score_TrimmedAbsoluteIntervallicStd": row[f"Score_{TRIMMED_ABSOLUTE_INTERVALLIC_STD}"],
            "Score_TrimmedIntervallicMean": row[f"Score_{TRIMMED_INTERVALLIC_MEAN}"],
            "Score_TrimmedIntervallicStd": row[f"Score_{TRIMMED_INTERVALLIC_STD}"],
            "Scoring": row[SCORING],
            "Score_Syllables": row[f"Score_{SYLLABLES}"],
            "Voices": row[VOICES],
        }
        for col in cols:
            if col.startswith("Score_Interval") and col.endswith("_Per"):
                data_item[col] = row[col]
            if col.startswith("Score_Degree") and col.endswith("_Per"):
                data_item[col] = row[col]
        for input_part, output_part in zip(input_parts_prefixes, output_parts_prefixes):
            for col in cols:
                if col.startswith(input_part) and "_Interval" in col and col.endswith("_Per"):
                    data_item[col.replace(input_part, output_part)] = row[col]
                if col.startswith(input_part) and "_Degree" in col and col.endswith("_Per"):
                    data_item[col.replace(input_part, output_part)] = row[col]
            data_item[f"{output_part}HighestNoteIndex"] = row[f"{input_part}{HIGHEST_NOTE_INDEX}"]
            data_item[f"{output_part}LowestNoteIndex"] = row[f"{input_part}{LOWEST_NOTE_INDEX}"]
            data_item[f"{output_part}Density"] = row[f"{input_part}{DENSITY}"]
            data_item[f"{output_part}SoundingDensity"] = row[f"{input_part}{SOUNDING_DENSITY}"]
            data_item[f"{output_part}IntervallicMean"] = row[f"{input_part}{INTERVALLIC_MEAN}"]
            data_item[f"{output_part}IntervallicStd"] = row[f"{input_part}{INTERVALLIC_STD}"]
            data_item[f"{output_part}IntervallicSkewness"] = row[f"{input_part}{INTERVALLIC_SKEWNESS}"]
            data_item[f"{output_part}IntervallicKurtosis"] = row[f"{input_part}{INTERVALLIC_KURTOSIS}"]
            data_item[f"{output_part}IntervallicTrimDiff"] = row[f"{input_part}{INTERVALLIC_TRIM_DIFF}"]
            data_item[f"{output_part}IntervallicTrimRatio"] = row[f"{input_part}{INTERVALLIC_TRIM_RATIO}"]
            data_item[f"{output_part}TrimmedIntervallicMean"] = row[f"{input_part}{TRIMMED_INTERVALLIC_MEAN}"]
            data_item[f"{output_part}TrimmedIntervallicStd"] = row[f"{input_part}{TRIMMED_INTERVALLIC_STD}"]
            data_item[f"{output_part}TrimmedAbsoluteIntervallicMean"] = row[f"{input_part}{TRIMMED_ABSOLUTE_INTERVALLIC_MEAN}"]
            data_item[f"{output_part}TrimmedAbsoluteIntervallicStd"] = row[f"{input_part}{TRIMMED_ABSOLUTE_INTERVALLIC_STD}"]
            data_item[f"{output_part}AbsoluteIntervallicMean"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_MEAN}"]
            data_item[f"{output_part}AbsoluteIntervallicStd"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_STD}"]
            data_item[f"{output_part}AbsoluteIntervallicSkewness"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_SKEWNESS}"]
            data_item[f"{output_part}AbsoluteIntervallicKurtosis"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_KURTOSIS}"]
            data_item[f"{output_part}AbsoluteIntervallicTrimDiff"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_TRIM_DIFF}"]
            data_item[f"{output_part}AbsoluteIntervallicTrimRatio"] = row[f"{input_part}{ABSOLUTE_INTERVALLIC_TRIM_RATIO}"]
            data_item[f"{output_part}AscendingIntervals"] = row[f"{input_part}{ASCENDING_INTERVALS_PER}"]
            data_item[f"{output_part}AscendingSemitonesSum"] = row[f"{input_part}{ASCENDING_SEMITONES_SUM}"]
            data_item[f"{output_part}DescendingIntervals"] = row[f"{input_part}{DESCENDING_INTERVALS_PER}"]
            data_item[f"{output_part}DescendingSemitonesSum"] = row[f"{input_part}{DESCENDING_SEMITONES_SUM}"]
            data_item[f"{output_part}IntervalsDiminishedAsc"] = row[f"{input_part}{INTERVALS_DIMINISHED_ASC_PER}"]
            data_item[f"{output_part}IntervalsDiminishedDesc"] = row[f"{input_part}{INTERVALS_DIMINISHED_DESC_PER}"]
            data_item[f"{output_part}IntervalsDiminishedAll"] = row[f"{input_part}{INTERVALS_DIMINISHED_ALL_PER}"]
            data_item[f"{output_part}IntervalsDoubleDiminishedAsc"] = row[f"{input_part}{INTERVALS_DOUBLE_DIMINISHED_ASC_PER}"]
            data_item[f"{output_part}IntervalsDoubleDiminishedDesc"] = row[f"{input_part}{INTERVALS_DOUBLE_DIMINISHED_DESC_PER}"]
            data_item[f"{output_part}IntervalsDoubleDiminishedAll"] = row[f"{input_part}{INTERVALS_DOUBLE_DIMINISHED_ALL_PER}"]
            data_item[f"{output_part}IntervalsMinorAsc"] = row[f"{input_part}{INTERVALS_MINOR_ASC_PER}"]
            data_item[f"{output_part}IntervalsMinorDesc"] = row[f"{input_part}{INTERVALS_MINOR_DESC_PER}"]
            data_item[f"{output_part}IntervalsMinorAll"] = row[f"{input_part}{INTERVALS_MINOR_ALL_PER}"]
            data_item[f"{output_part}IntervalsPerfectAsc"] = row[f"{input_part}{INTERVALS_PERFECT_ASC_PER}"]
            data_item[f"{output_part}IntervalsPerfectDesc"] = row[f"{input_part}{INTERVALS_PERFECT_DESC_PER}"]
            data_item[f"{output_part}IntervalsPerfectAll"] = row[f"{input_part}{INTERVALS_PERFECT_ALL_PER}"]
            data_item[f"{output_part}IntervalsMajorAsc"] = row[f"{input_part}{INTERVALS_MAJOR_ASC_PER}"]
            data_item[f"{output_part}IntervalsMajorDesc"] = row[f"{input_part}{INTERVALS_MAJOR_DESC_PER}"]
            data_item[f"{output_part}IntervalsMajorAll"] = row[f"{input_part}{INTERVALS_MAJOR_ALL_PER}"]
            data_item[f"{output_part}IntervalsAugmentedAsc"] = row[f"{input_part}{INTERVALS_AUGMENTED_ASC_PER}"]
            data_item[f"{output_part}IntervalsAugmentedDesc"] = row[f"{input_part}{INTERVALS_AUGMENTED_DESC_PER}"]
            data_item[f"{output_part}IntervalsAugmentedAll"] = row[f"{input_part}{INTERVALS_AUGMENTED_ALL_PER}"]
            data_item[f"{output_part}IntervalsDoubleAugmentedAsc"] = row[f"{input_part}{INTERVALS_DOUBLE_AUGMENTED_ASC_PER}"]
            data_item[f"{output_part}IntervalsDoubleAugmentedDesc"] = row[f"{input_part}{INTERVALS_DOUBLE_AUGMENTED_DESC_PER}"]
            data_item[f"{output_part}IntervalsDoubleAugmentedAll"] = row[f"{input_part}{INTERVALS_DOUBLE_AUGMENTED_ALL_PER}"]
            data_item[f"{output_part}IntervalsBeyondOctaveAsc"] = row[f"{input_part}{INTERVALS_BEYOND_OCTAVE_ASC_PER}"]
            data_item[f"{output_part}IntervalsBeyondOctaveDesc"] = row[f"{input_part}{INTERVALS_BEYOND_OCTAVE_DESC_PER}"]
            data_item[f"{output_part}IntervalsBeyondOctaveAll"] = row[f"{input_part}{INTERVALS_BEYOND_OCTAVE_ALL_PER}"]
            data_item[f"{output_part}IntervalsWithinOctaveAsc"] = row[f"{input_part}{INTERVALS_WITHIN_OCTAVE_ASC_PER}"]
            data_item[f"{output_part}IntervalsWithinOctaveDesc"] = row[f"{input_part}{INTERVALS_WITHIN_OCTAVE_DESC_PER}"]
            data_item[f"{output_part}IntervalsWithinOctaveAll"] = row[f"{input_part}{INTERVALS_WITHIN_OCTAVE_ALL_PER}"]
            data_item[f"{output_part}LeapsAsc"] = row[f"{input_part}{LEAPS_ASC_PER}"]
            data_item[f"{output_part}LeapsDesc"] = row[f"{input_part}{LEAPS_DESC_PER}"]
            data_item[f"{output_part}LeapsAll"] = row[f"{input_part}{LEAPS_ALL_PER}"]
            data_item[f"{output_part}StepwiseMotionAsc"] = row[f"{input_part}{STEPWISE_MOTION_ASC_PER}"]
            data_item[f"{output_part}StepwiseMotionDesc"] = row[f"{input_part}{STEPWISE_MOTION_DESC_PER}"]
            data_item[f"{output_part}StepwiseMotionAll"] = row[f"{input_part}{STEPWISE_MOTION_ALL_PER}"]
            data_item[f"{output_part}RepeatedNotes"] = row[f"{input_part}{REPEATED_NOTES_PER}"]
            data_item[f"{output_part}LargestSemitonesAll"] = row[f"{input_part}{LARGEST_SEMITONES_ALL}"]
            data_item[f"{output_part}LargestSemitonesAsc"] = row[f"{input_part}{LARGEST_SEMITONES_ASC}"]
            data_item[f"{output_part}LargestSemitonesDesc"] = row[f"{input_part}{LARGEST_SEMITONES_DESC}"]
            data_item[f"{output_part}LargestAbsoluteSemitonesAll"] = row[f"{input_part}{LARGEST_ABSOLUTE_SEMITONES_ALL}"]
            data_item[f"{output_part}LargestAbsoluteSemitonesAsc"] = row[f"{input_part}{LARGEST_ABSOLUTE_SEMITONES_ASC}"]
            data_item[f"{output_part}LargestAbsoluteSemitonesDesc"] = row[f"{input_part}{LARGEST_ABSOLUTE_SEMITONES_DESC}"]
            data_item[f"{output_part}SmallestSemitonesAll"] = row[f"{input_part}{SMALLEST_SEMITONES_ALL}"]
            data_item[f"{output_part}SmallestSemitonesAsc"] = row[f"{input_part}{SMALLEST_SEMITONES_ASC}"]
            data_item[f"{output_part}SmallestSemitonesDesc"] = row[f"{input_part}{SMALLEST_SEMITONES_DESC}"]
            data_item[f"{output_part}SmallestAbsoluteSemitonesAll"] = row[f"{input_part}{SMALLEST_ABSOLUTE_SEMITONES_ALL}"]
            data_item[f"{output_part}SmallestAbsoluteSemitonesAsc"] = row[f"{input_part}{SMALLEST_ABSOLUTE_SEMITONES_ASC}"]
            data_item[f"{output_part}SmallestAbsoluteSemitonesDesc"] = row[f"{input_part}{SMALLEST_ABSOLUTE_SEMITONES_DESC}"]
        data_list.append(data_item)
    df_analysis = pd.DataFrame(data_list)
    df_analysis.sort_values("AriaId", inplace=True)
    df_analysis.to_csv("analysis4_Perez_Galuppi.csv", index=False)
    print(df_analysis.shape[1])
