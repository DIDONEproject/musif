# import os
import sys

sys.path.insert(0, "../musif/")
from musif.process.utils import merge_dataframes
import os
import pandas as pd
from musif.extract.extract import FeaturesExtractor
from musif.process.processor import DataProcessor
from musif.process.filter import DataFilter


    
if __name__ == "__main__":
    print('\nUpdating metadata files...')
    os.system("python scripts/metadata_updater.py")
    data_dir = r'../Half_Corpus/xml'
    musescore_dir = r'../../_Ana\Music Analysis/xml/corpus_github/musescore'
    check_file = None
    
    name = "features_14_06"
    # df = FeaturesExtractor("scripts/config_drive.yml", data_dir=data_dir, musescore_dir=musescore_dir, check_file=check_file).extract()
    prefix='martiser/'
    dest_path = prefix + name + "_total" + ".csv"
    # merge_dataframes(prefix + name, dest_path)
    
    p = DataProcessor(dest_path, "scripts/post_process.yml", merge_voices=True)
    print(p.data.shape)
    p.process()
    print('Final shape is: ', p.data.shape)
    
    filter_list=['Misero_pargoletto', 'Se_tutti', 'Son_regina', 'Non_ha', 'Se_resto', 'Ah_non_lasciarmi', 'Cadra_fra']
    f = DataFilter('total_processed.csv').filter_data(by='AriaName', equal_to=filter_list, instrument='SoundVoice')
    
    # Methods to test
    # p.delete_previous_items()
    # print(p.data.columns[p.data.columns.str.contains('Key')])
    # print(p.data.columns[p.data.columns.str.contains('Key')].shape)
    # p._group_keys()
    # print(p.data.columns[p.data.columns.str.contains('Key')])
    # p.delete_unwanted_columns(columns_endswith=['Per'])
    # p.to_csv('final_features.csv')
    i=1