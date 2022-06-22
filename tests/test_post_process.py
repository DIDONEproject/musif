from os import path

import pandas as pd
import pytest
from musif.config import PostProcess_Configuration
from musif.extract.features.harmony.constants import CHORD_prefix
from musif.extract.features.prefix import get_part_prefix
from musif.process.processor import DataProcessor

from tests.constants import CONFIG_PATH, DATA_STATIC_DIR, TEST_FILE
import os

name = "features_14_06"
dest_path = 'martiser/' + name + "_total" + '_features'

processed_file_path = path.join(dest_path+'.csv')

postconfig_path = path.join(CONFIG_PATH, "post_process.yml")

data_features_dir = path.join(DATA_STATIC_DIR, "features")
reference_file_path = path.join(data_features_dir, 'features_example.csv')


@pytest.fixture(scope="session")
def processed_data():
    if os.path.exists(processed_file_path):
        processed = DataProcessor(processed_file_path, postconfig_path)
        # processed_df = processed_df[processed_df['AriaId'].notna()]
        yield processed.data
    else:
        raise Exception('Extracted file could not be found.')
    
@pytest.fixture(scope="session")
def process_object():
    processor = DataProcessor(processed_file_path, postconfig_path)
    yield processor
    
@pytest.fixture(scope="session")
def post_process_configuration():
    yield DataProcessor(processed_file_path, postconfig_path)._post_config


class TestPostProcess:
    def test_wrong_path(self):
        # with pytest.raises(Exception) as excinfo:
        with pytest.raises(FileNotFoundError, match='The .csv file could not be found.'):
            DataProcessor('wrong_path.csv')._process_info
            raise FileNotFoundError('The .csv file could not be found.')
    
    # def test_no_config_file(self):
    #     with pytest.raises(FileNotFoundError, match='A post_config.yml file or a dictionary is needed to instantate the class'):
    #         DataProcessor(reference_file_path, 'no_config.yml')
    #         raise FileNotFoundError('A post_config.yml file or a dictionary is needed to instantate the class')
        

class TestProcessedFile:
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
        
    def test_not_nan_values(self, processed_data: pd.DataFrame):
        assert not processed_data.isnull().values.any()
        
    def test_ensure_violin_solo_not_present(self, processed_data: pd.DataFrame):
        assert len([i for i in processed_data if i.startswith('PartVn_')])==0
        
    def test_intruders_in_df(self, processed_data: pd.DataFrame, post_process_configuration: PostProcess_Configuration):
        intruders = []
        for i in processed_data.columns:
            if i.endswith(tuple(post_process_configuration.columns_endswith)):
                intruders.append(i)
        assert len(intruders) == 0
        
    def test_tonic_chord_not_empty(self, processed_data: pd.DataFrame):
        assert not all([i<0.1 for i in processed_data[CHORD_prefix+'I_Per']])
        
    def test_no_part_texture(self, process_object: pd.DataFrame, processed_data: pd.DataFrame):
        config = process_object._post_config
        columns_to_examine = [i for i in processed_data if 'Part' in i and not 'Texture' in i]
        prefixes = tuple(get_part_prefix(x) for x in config.instruments_to_keep)
        assert all([i.startswith(prefixes) for i in columns_to_examine if i])
