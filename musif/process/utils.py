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
)
from musif.extract.features.prefix import get_part_prefix
from musif.extract.features.scale.constants import DEGREE_PREFIX
from musif.logs import pinfo

from .constants import voices_list_prefixes


def join_part_degrees(
    total_degrees: List[str], part: str, df: DataFrame, sufix: str = ""
) -> None:
    """Group one prefix's per-degree columns into Asc/Desc/Dasc/Ddesc/Nat/Nonat
    aggregates, separately for _Count and _Per columns.

    The accidental is matched as a token of the column name (not a substring),
    so prefixes containing 'b' or 'x' (PartOb_, PartTbn_, ...) cannot
    contaminate the groups.
    """
    pattern = re.compile(
        re.escape(part) + r"Degree(b+|#x?|x)?(\d+)_(Count|Per)" + re.escape(sufix) + "$"
    )
    for kind in ("Count", "Per"):
        selected = {name: [] for name in ("Asc", "Desc", "Dasc", "Ddesc", "Nat", "Nonat")}
        for col in total_degrees:
            match = pattern.fullmatch(col)
            if match is None or match.group(3) != kind:
                continue
            accidental = match.group(1) or ""
            if accidental == "":
                selected["Nat"].append(col)
            else:
                selected["Nonat"].append(col)
                if accidental == "#":
                    selected["Asc"].append(col)
                elif accidental == "b":
                    selected["Desc"].append(col)
                elif accidental in ("x", "#x"):
                    selected["Dasc"].append(col)
                else:  # bb, bbb, ...
                    selected["Ddesc"].append(col)
        if not any(selected.values()):
            continue
        for name, cols in selected.items():
            column = part + DEGREE_PREFIX + "_" + name + "_" + kind + sufix
            df[column] = df[cols].sum(axis=1) if cols else 0.0


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
