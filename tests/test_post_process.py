import math
import re
from os import path

import pandas as pd
import pytest
from musif.extract.features.prefix import get_part_prefix

from musif.process.processor import DataProcessor
from tests.constants import TEST_FILE, DATA_STATIC_DIR,CONFIG_PATH

extracted_file = 'features_14_06'
processed_file = extracted_file+'_features'

postconfig_path = path.join(CONFIG_PATH, "post_process.yml")
extracted_csv = path.join(DATA_STATIC_DIR, extracted_file+'.csv')

data_features_dir = path.join(DATA_STATIC_DIR, "features")
reference_file_path = path.join(data_features_dir, TEST_FILE)

processed_file_path= path.join(processed_file+'.csv')

@pytest.fixture(scope="session")
def processed_data():
    processed_df = DataProcessor(extracted_csv, postconfig_path).process()
    processed_df = processed_df[processed_df['AriaId'].notna()]
    yield processed_df
    
@pytest.fixture(scope="session")
def process_object():
    processed_df = DataProcessor(extracted_csv, postconfig_path)
    yield processed_df
    
@pytest.fixture(scope="session")
def extracted_file():
    analyzed_file = pd.read_csv(processed_file_path)
    yield analyzed_file

class TestPostProcess:
    def test_tonic_chord_not_empty(self, extracted_file: pd.DataFrame):
        assert not all([i<0.1 for i in extracted_file['Chord_I_Per']])
        
    def test_intruders_in_df(self, processed_data: pd.DataFrame):
        intruders = []
        for i in ['FamilyGen', 'Instrumentation', 'Scoring']:
            if i in processed_data:
                    intruders.append(i)
        assert len(intruders) == 0, intruders
            
    def test_only_desired_instruments(self, process_object: pd.DataFrame, processed_data: pd.DataFrame):
        config=process_object._post_config
        columns_to_examine = [i for i in processed_data if 'Part' in i and not 'Texture' in i]
        prefixes=tuple(get_part_prefix(x) for x in config.instruments_to_keep)
        assert all([i.startswith(prefixes) for i in columns_to_examine if i])

    def test_ensure_violin_solo_not_present(self, processed_data: pd.DataFrame):
        assert len([i for i in processed_data if i.startswith('PartVn_')])==0
        
    def test_column_types_match(self, processed_data: pd.DataFrame):
        found_cols = []
        for col in processed_data.columns:
            if col in found_cols:
                continue
            weird = (processed_data[[col]].applymap(type) != processed_data[[col]].iloc[0].apply(type)).any(axis=1)
            if len(processed_data[weird]) > 0:
                found_cols.append(col)
                print('\n---\n')
                print(col)
                indices = weird[weird]
                print(indices.index)
        assert not found_cols
