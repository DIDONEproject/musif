import re
from logging.config import dictConfig
from typing import List

import pandas as pd
from pandas import DataFrame

from musif.config import (
    ENDSWITH,
    INSTRUMENTS_TO_DELETE,
    INSTRUMENTS_TO_KEEP,
    STARTSWITH,
)
from musif.extract.basic_modules.scoring.constants import (
    FAMILY_INSTRUMENTATION,
    FAMILY_SCORING,
)
from musif.extract.features.harmony.constants import (
    KEY_MODULATORY,
    KEY_PERCENTAGE,
    KEY_PREFIX,
    CHORD_prefix,
)
from musif.extract.features.melody.constants import TRIMMED_INTERVALLIC_MEAN
from musif.extract.features.prefix import get_part_prefix
from musif.extract.features.scale.constants import DEGREE_PREFIX
from musif.logs import pinfo

from .constants import voices_list_prefixes


def replace_nans(df):
    for col in df.columns:
        if (
            "Interval" in col
            or col.startswith("Key_")
            or col.startswith((CHORD_prefix, "Chords_", "Additions_", "Numerals_"))
            or col.endswith(("_DottedRhythm", "_DoubleDottedRhythm"))
            or ("_Degree" and TRIMMED_INTERVALLIC_MEAN and "_Dyn") in col
        ):
            df[col] = df[col].fillna("NA")


def join_part_degrees(
    total_degrees: List[str], part: str, df: DataFrame, sufix: str = ""
) -> None:
    part_degrees = [i for i in total_degrees if part in i]

    aug = [i for i in part_degrees if "#" in i]
    desc = [i for i in part_degrees if "b" in i and "bb" not in i]
    d_desc = [i for i in part_degrees if "bb" in i]
    d_asc = [i for i in part_degrees if "x" in i]

    pattern = "^" + part + "Degree" + "[0-9].*"
    degree_nat = [x for x in part_degrees if re.search(pattern, x)]
    degree_nonat = [i for i in part_degrees if i not in degree_nat]

    df[part + DEGREE_PREFIX + "_Asc" + sufix] = df[aug].sum(axis=1)
    df[part + DEGREE_PREFIX + "_Desc" + sufix] = df[desc].sum(axis=1)
    df[part + DEGREE_PREFIX + "_Dasc" + sufix] = df[d_asc].sum(axis=1)
    df[part + DEGREE_PREFIX + "_Ddesc" + sufix] = df[d_desc].sum(axis=1)
    df[part + DEGREE_PREFIX + "_Nat" + sufix] = df[degree_nat].sum(axis=1)
    df[part + DEGREE_PREFIX + "_Nonat" + sufix] = df[degree_nonat].sum(axis=1)


def log_errors_and_shape(
    composer_counter: list, novoices_counter: list, df: DataFrame
) -> None:
    pinfo(f"\nTotal files skipped by composer: {len(composer_counter)}")
    pinfo(str(composer_counter))
    pinfo(f"\nTotal files skipped by no-voices: { len(novoices_counter)}")
    pinfo(str(novoices_counter))
    # pinfo(f"\nTotal files skipped by duetos/trietos: {len(duetos_counter)}")
    # pinfo(str(duetos_counter))
    pinfo(f"\nFinal shape of the DataFrame: {df.shape[0]} rows, {df.shape[1]} features")


def _delete_columns(data: DataFrame, config: dictConfig) -> None:
    # pinfo("\nDeleting not useful columns...")
    to_delete = []
    instruments_to_keep = [get_part_prefix(i) for i in config[INSTRUMENTS_TO_KEEP]]
    for inst in config[INSTRUMENTS_TO_DELETE]:
        # for i in data.columns:
        #     if "Part" + inst + "_" in i
        part_prefix = "Part" + inst  # + "_"
        for col in data.columns:
            if part_prefix in col and all(
                inst not in col for inst in instruments_to_keep
            ):
                pass
                to_delete.append(col)
            else:
                pass
        # to_delete += [i for i in data.columns if part_prefix in i and instrument not in i for instrument in instruments_to_keep]

    to_delete += [i for i in data.columns if i.endswith(tuple(config[ENDSWITH]))]
    to_delete += [i for i in data.columns if i.startswith(tuple(config[STARTSWITH]))]
    to_delete += [
        col
        for col in data.columns
        if any(substring in col for substring in config["columns_contain"])
    ]
    to_delete += [
        col
        for col in data.columns
        if any(string == col for string in config["columns_match"])
    ]
    to_delete += [i for i in data.columns if i.startswith("Sound") and "Voice" not in i]

    to_delete += [FAMILY_INSTRUMENTATION, FAMILY_SCORING]

    # Remove empty voices
    to_delete += [
        col
        for col in data.columns
        if col.startswith(tuple(voices_list_prefixes))
        and all(data[col].isnull().values)
    ]

    # removing columns containing nans
    if config['delete_columns_with_nans']:
        th = config["max_nan_columns"] or 0.0
        idx = data.isna().sum(axis=0) / data.shape[0] > th
        to_delete += data.columns[idx].to_list()

    data.drop(columns=to_delete, inplace=True, errors="ignore")


def join_keys(df: DataFrame) -> None:
    key_SD = [
        i
        for i in [
            KEY_PREFIX + "IV" + KEY_PERCENTAGE,
            KEY_PREFIX + "II" + KEY_PERCENTAGE,
            KEY_PREFIX + "VI" + KEY_PERCENTAGE,
        ]
        if i in df
    ]
    key_sd = [
        i
        for i in [
            KEY_PREFIX + "iv" + KEY_PERCENTAGE,
            KEY_PREFIX + "ii" + KEY_PERCENTAGE,
        ]
        if i in df
    ]
    key_tonic = [
        i
        for i in [KEY_PREFIX + "I" + KEY_PERCENTAGE, KEY_PREFIX + "i" + KEY_PERCENTAGE]
        if i in df
    ]
    key_rel = [
        i
        for i in [
            KEY_PREFIX + "III" + KEY_PERCENTAGE,
            KEY_PREFIX + "vi" + KEY_PERCENTAGE,
        ]
        if i in df
    ]

    total_key = key_rel + key_tonic + key_sd + key_SD
    others_key = [
        i
        for i in df.columns
        if KEY_PREFIX in i and i not in total_key and KEY_MODULATORY not in i
    ]

    df[KEY_PREFIX + "SD" + KEY_PERCENTAGE] = df[key_SD].sum(axis=1)
    df[KEY_PREFIX + "sd" + KEY_PERCENTAGE] = df[key_sd].sum(axis=1)
    df[KEY_PREFIX + "SubD" + KEY_PERCENTAGE] = (
        df[KEY_PREFIX + "sd" + KEY_PERCENTAGE] + df[KEY_PREFIX + "SD" + KEY_PERCENTAGE]
    )
    df[KEY_PREFIX + "T" + KEY_PERCENTAGE] = df[key_tonic].sum(axis=1)
    df[KEY_PREFIX + "rel" + KEY_PERCENTAGE] = df[key_rel].sum(axis=1)
    df[KEY_PREFIX + "Other" + KEY_PERCENTAGE] = df[others_key].sum(axis=1)
    # df.drop(total_key + others_key, axis = 1, inplace=True)


def join_keys_modulatory(df: DataFrame):
    key_SD = [
        i
        for i in [
            KEY_PREFIX + KEY_MODULATORY + "IV",
            KEY_PREFIX + KEY_MODULATORY + "II",
            KEY_PREFIX + KEY_MODULATORY + "VI",
        ]
        if i in df
    ]
    key_sd = [
        i
        for i in [
            KEY_PREFIX + KEY_MODULATORY + "iv",
            KEY_PREFIX + KEY_MODULATORY + "ii",
        ]
        if i in df
    ]
    key_tonic = [
        i
        for i in [KEY_PREFIX + KEY_MODULATORY + "I", KEY_PREFIX + KEY_MODULATORY + "i"]
        if i in df
    ]
    key_rel = [
        i
        for i in [
            KEY_PREFIX + KEY_MODULATORY + "III",
            KEY_PREFIX + KEY_MODULATORY + "vi",
        ]
        if i in df
    ]

    total_key_mod = key_rel + key_tonic + key_sd + key_SD
    others_key_mod = [
        i
        for i in df.columns
        if KEY_PREFIX + KEY_MODULATORY in i and i not in total_key_mod
    ]

    df[KEY_PREFIX + KEY_MODULATORY + "SD"] = df[key_SD].sum(axis=1)
    df[KEY_PREFIX + KEY_MODULATORY + "sd"] = df[key_sd].sum(axis=1)
    df[KEY_PREFIX + KEY_MODULATORY + "SubD"] = (
        df[KEY_PREFIX + KEY_MODULATORY + "sd"] + df[KEY_PREFIX + KEY_MODULATORY + "SD"]
    )
    df[KEY_PREFIX + KEY_MODULATORY + "T"] = df[key_tonic].sum(axis=1)
    df[KEY_PREFIX + KEY_MODULATORY + "rel"] = df[key_rel].sum(axis=1)
    df[KEY_PREFIX + KEY_MODULATORY + "Other"] = df[others_key_mod].sum(axis=1)

def _drop_filenames_nan_rows(df):
    rows_with_nan_filename = list(df[df['FileName'].isna()]['FileName'].index)
    if len(rows_with_nan_filename)>0:
        print('There are som files with computation errors!')
        print(rows_with_nan_filename)
        df.dropna(subset=['FileName'], inplace=True)

def merge_dataframes(name: str, dest_path: str) -> None:
    """
    Takes two dataframes and joins them, apart from deleting rows that are all nans.
    This is intended for cases where all extraction of a folder cannot be done all at once.
    
    Returns
    ------
    Dataframe with the extracted features as a concatenation of two dataframes
    """
    csv = ".csv"
    name1 = name + "_1" + csv
    name2 = name + "_2" + csv

    df1 = pd.read_csv(name1, low_memory=False)
    df2 = pd.read_csv(name2, low_memory=False)
    
    _drop_filenames_nan_rows(df1)
    _drop_filenames_nan_rows(df2)
    
    total_dataframe = pd.concat((df1, df2), axis=0)
    total_dataframe.to_csv(dest_path + csv, index=False)
