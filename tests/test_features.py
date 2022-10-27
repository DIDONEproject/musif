import math
import re
from os import path

import pandas as pd
import pytest

from musif import FeaturesExtractor
from musif.common._utils import read_dicts_from_csv
from musif.extract.features.prefix import get_family_prefix, get_part_prefix, get_sound_prefix
from musif.basic_modules.scoring.constants import NUMBER_OF_FILTERED_PARTS, NUMBER_OF_PARTS
from .constants import BASE_PATH, DATA_STATIC_DIR

config_path = path.join(DATA_STATIC_DIR, "config.yml")
data_features_dir = path.join(DATA_STATIC_DIR, "features")
reference_file_path = path.join(data_features_dir, "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")
expected_features_file_path = path.join(data_features_dir, "expected_features.csv")


@pytest.fixture(scope="session")
def actual_data():
    data_df = FeaturesExtractor(config_path, data_dir=data_features_dir, parts_filter=None).extract()
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
            errors += "\nColumns in CSV, but missing in DataFrame\n" + not_in_actual_data
        not_in_expected_data = ""
        for col in actual_columns:
            if col not in expected_data:
                not_in_expected_data += f'  {col}\n'
        if len(not_in_expected_data) > 0:
            errors += "\nColumns in DataFrame, but missing in CSV\n" + not_in_expected_data

        # Then
        assert len(errors) == 0, errors

    def test_values_match(self, actual_data: pd.DataFrame, expected_data: dict):
        errors = ""
        for col in actual_data.columns:
            data_type = str(actual_data.dtypes[col])
            actual_value = format_value(actual_data[col].values[0], data_type)
            expected_value = format_value(expected_data.get(col), data_type)
            if actual_value != expected_value:
                errors += f'\t{col}\n\t\tCSV      : {expected_value}\n\t\tDataFrame: {actual_value}\n'
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
    part_feature_pattern = ".*" + get_part_prefix(".+")
    sound_feature_pattern = ".*" + get_sound_prefix(".+")
    family_feature_pattern = ".*" + get_family_prefix(".+")
    for col in df.columns:
        # Keep all scoring features
        if col.endswith(NUMBER_OF_FILTERED_PARTS) or col.endswith(NUMBER_OF_PARTS):
            continue
        #Exception for texture
        if col=='PartVoice__PartVnI__Texture':
            continue
        col_without_part = col.replace(get_part_prefix("VnI"), "")
        col_without_part = col_without_part.replace(get_part_prefix("Sop"), "")
        if re.match(part_feature_pattern, col_without_part):
            cols_to_remove.append(col)
        col_without_sound = col.replace(get_sound_prefix("Vn"), "")
        col_without_sound = col_without_sound.replace(get_sound_prefix("Sop"), "")
        if re.match(sound_feature_pattern, col_without_sound):
            cols_to_remove.append(col)
        col_without_family = col.replace(get_family_prefix("Str"), "")
        col_without_family = col_without_family.replace(get_family_prefix("Voice"), "")
        if re.match(family_feature_pattern, col_without_family):
            cols_to_remove.append(col)
    df.drop(cols_to_remove, axis=1, inplace=True)
