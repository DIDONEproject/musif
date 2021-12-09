import math
from os import path

import pandas as pd
import pytest

from musif import FeaturesExtractor
from musif.common.utils import read_dicts_from_csv
from musif.extract.features.prefix import get_family_prefix, get_part_prefix, get_sound_prefix
from musif.extract.features.scoring.constants import NUMBER_OF_FILTERED_PARTS, NUMBER_OF_PARTS, SOUND_SCORING

data_static_dir = path.join("data", "static")
config_path = path.join(data_static_dir, "config.yml")
data_features_dir = path.join(data_static_dir, "features")
reference_file_path = path.join(data_features_dir, "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")
expected_features_file_path = path.join(data_features_dir, "expected_features.csv")


@pytest.fixture(scope="session")
def actual_data():
    parts_filter = None
    extractor = FeaturesExtractor(config_path, data_dir=data_features_dir, parts_filter=parts_filter)
    data_df = extractor.extract()
    remove_columns_not_being_tested(data_df)
    yield data_df

@pytest.fixture(scope="session")
def expected_data():
    expected_data = read_dicts_from_csv(expected_features_file_path)[0]
    yield expected_data


class TestFeatures:

    def test_columns_match(self, actual_data: pd.DataFrame, expected_data: dict):
        # Given

        # When
        errors = ""
        not_in_actual_data = ""
        actual_columns = sorted(actual_data.columns.tolist())
        for col in expected_data.keys():
            if col not in actual_columns:
                not_in_actual_data += f'\t{col}\n'
        if len(not_in_actual_data) > 0:
            errors += "\nColumns in expected data, but missing in actual data\n" + not_in_actual_data
        not_in_expected_data = ""
        for col in actual_columns:
            if col not in expected_data:
                not_in_expected_data += f'  {col}\n'
        if len(not_in_actual_data) > 0:
            errors += "\nColumns in actual data, but missing in expected data\n" + not_in_expected_data

        # Then
        assert len(errors) == 0, errors

    def test_values_match(self, actual_data: pd.DataFrame, expected_data: dict):
        # Given

        # When
        errors = ""
        for col in actual_data.columns:
            data_type = str(actual_data.dtypes[col])
            actual_value = format_value(actual_data[col].values[0], data_type)
            expected_value = format_value(expected_data.get(col), data_type)
            if actual_value != expected_value:
                errors += f'\t{col}\n\t\tExpected: {expected_value}\n\t\tActual:   {actual_value}\n'
        if len(errors) > 0:
            errors = f"\nThese values are wrong:\n\n{errors}"

        # Then
        assert len(errors) == 0, errors


def format_value(value, data_type: str):
    try:
        if data_type == 'object':
            return str(value) if value is not None else ""
        if data_type.startswith("float"):
            return round(float(value), 3) if value is not None else 0.0
        if data_type.startswith("int"):
            return math.floor(float(value)) if value is not None else 0
    except:
        ...
    return None

def remove_columns_not_being_tested(df: pd.DataFrame) -> None:
    cols_to_remove = []
    for col in df.columns:
        # Keep all scoring features
        if col.endswith(NUMBER_OF_FILTERED_PARTS) or col.endswith(NUMBER_OF_PARTS):
            continue
        if col.startswith(get_part_prefix("")) and "_" in col:
            if not col.startswith(get_part_prefix("vnI")) and not col.startswith(get_part_prefix("sop")):
                cols_to_remove.append(col)
        if col.startswith(get_sound_prefix("")) and "_" in col:
            if not col.startswith(get_sound_prefix("vn")) and not col.startswith(get_sound_prefix("sop")):
                cols_to_remove.append(col)
        if col.startswith(get_family_prefix("")) and "_" in col:
            if not col.startswith(get_family_prefix("Str")) and not col.startswith(get_family_prefix("Voice")):
                cols_to_remove.append(col)
    df.drop(cols_to_remove, axis=1, inplace=True)
