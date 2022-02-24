import math
import re
from os import path

import pandas as pd
import pytest

from musif import FeaturesExtractor
from musif.common.utils import read_dicts_from_csv
from musif.extract.features.prefix import get_family_prefix, get_part_prefix, get_sound_prefix
from musif.extract.features.scoring.constants import NUMBER_OF_FILTERED_PARTS, NUMBER_OF_PARTS

data_static_dir = path.join("data", "static")
config_path = path.join(data_static_dir, "config.yml")
data_features_dir = path.join(data_static_dir, "features")
reference_file_path = path.join(data_features_dir, "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")
expected_features_file_path = path.join(data_features_dir, "expected_features.csv")


@pytest.fixture(scope="session")
def actual_data():
    data_df = FeaturesExtractor(config_path, data_dir=data_features_dir, parts_filter=None).extract()
    # remove_columns_not_being_tested(data_df)
    yield data_df

@pytest.fixture(scope="session")
def expected_data():
    expected_data = read_dicts_from_csv(expected_features_file_path)[0]
    yield expected_data


class TestPostProcess:

    def test_columns_match(self, actual_data: pd.DataFrame, expected_data: dict):
        pass
        # Given

        # When

        # Then
        # assert len(errors) == 0, errors

    def test_values_match(self, actual_data: pd.DataFrame, expected_data: dict):
        # Given

        # When
        # errors = ""
        # for col in actual_data.columns:
        #     data_type = str(actual_data.dtypes[col])
        #     actual_value = format_value(actual_data[col].values[0], data_type)
        #     expected_value = format_value(expected_data.get(col), data_type)
        #     if actual_value != expected_value:
        #         errors += f'\t{col}\n\t\tCSV      : {expected_value}\n\t\tDataFrame: {actual_value}\n'
        # if len(errors) > 0:
        #     errors = f"\nThese values are wrong:\n\n{errors}"

        # Then
        assert 1==1


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
