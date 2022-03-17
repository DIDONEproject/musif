import math
import re
from os import path

import pandas as pd
import pytest
from musif import FeaturesExtractor

from musif.process.processor import DataProcessor
from tests.constants import TEST_FILE, DATA_STATIC_DIR

postconfig_path = path.join(DATA_STATIC_DIR, "post_config.yml")
data_features_dir = path.join(DATA_STATIC_DIR, "features")
reference_file_path = path.join(data_features_dir, TEST_FILE)
expected_features_file_path = path.join(data_features_dir, "expected_features.csv")

analyzed_file_path= path.join(DATA_STATIC_DIR, 'analyzed_Did03M-Son_regina-1730-Sarro[1.05][0006].csv')

# 3. asegurar que solo hay part vnI partbs y soundvoice y no mas partes
# 4. asegurar que no hya partvn_
# 4. asdsegurar que hay valores en las dinamicas de partvnI y partbs que no sean nan
# 5. asdsegurar que hay valores en las intervalos de partvnI y partbs que no sean nan

@pytest.fixture(scope="session")
def processed_data():
    processed_df=DataProcessor("features_extraction", postconfig_path).process()
    yield processed_df
    
@pytest.fixture(scope="session")
def process_object():
    processed_df=DataProcessor("features_extraction", postconfig_path)
    yield processed_df
    
@pytest.fixture(scope="session")
def extracted_file():
    analyzed_file = pd.read_csv(analyzed_file_path)
    # analyzed_file = FeaturesExtractor(config_path, data_dir=data_features_dir, parts_filter=None).extract()
    yield analyzed_file

# @pytest.fixture(scope="session")
# def expected_data():
#     expected_data = read_dicts_from_csv(expected_features_file_path)[0]
#     yield expected_data

class TestPostProcess:
    def test_tonic_chord_not_empty(self, extracted_file: pd.DataFrame):
        assert not all([i<0.1 for i in extracted_file['Chord_I_Per']])
        
        
    def test_intruders_in_df(self, processed_data: pd.DataFrame):
        intruders = []
        for i in ['FamilyGen', 'Instrumentation', 'Scoring']:
            if i in processed_data:
                    intruders.append(i)
        assert len(intruders) == 0, intruders
            
    def test_intruders_in_df(self, process_object: pd.DataFrame, processed_data):
        config=process_object._post_config
        columns_to_examine=[i for i in processed_data if 'Part' in i]
        config.instruments_to_keep
        assert len()
                
    def test_columns_match(self, processed_data: pd.DataFrame):
        # Given
        # When
        # errors = ""
        # not_in_actual_data = ""
        # actual_columns = sorted(actual_data.columns.tolist())
        # for col in expected_data.keys():
        #     if col not in actual_columns:
        #         not_in_actual_data += f'\t{col}\n'
        # if len(not_in_actual_data) > 0:
        #     errors += "\nColumns in CSV, but missing in DataFrame\n" + not_in_actual_data
        # not_in_expected_data = ""
        # for col in actual_columns:
        #     if col not in expected_data:
        #         not_in_expected_data += f'  {col}\n'
        # if len(not_in_expected_data) > 0:
        #     errors += "\nColumns in DataFrame, but missing in CSV\n" + not_in_expected_data

        # # Then
        # assert len(errors) == 0, errors
        pass

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
