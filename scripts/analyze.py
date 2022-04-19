import os
import sys
sys.path.insert(0, "../")

from musif.extract.extract import FeaturesExtractor
from musif.process.processor import DataProcessor


if __name__ == "__main__":
    print('\nUpdating metadata files...')
    os.system("python scripts/metadata_updater.py")
    data_dir = r'../Half_Corpus/xml'
    musescore_dir = r'../../_Ana\Music Analysis/xml/corpus_github/musescore'
    # check_file = 'parsed_files_total.csv'
    check_file=None
    name = "features_total_1_04"
    # df = FeaturesExtractor("scripts/config_drive.yml", data_dir=data_dir, musescore_dir=musescore_dir, check_file=check_file).extract()
    
    dest_path=name+"_extraction.csv"
    # df.to_csv(dest_path, index=False)
    
    p=DataProcessor(dest_path, "scripts/post_process.yml", merge_voices=True)
    p.process()

    # Methods to test
    # print(p.data.shape)
    # p.delete_previous_items()
    # print(p.data.columns[p.data.columns.str.contains('Key')])
    # print(p.data.columns[p.data.columns.str.contains('Key')].shape)
    # p._group_keys()
    # print(p.data.columns[p.data.columns.str.contains('Key')])
    # p.delete_unwanted_columns(columns_endswith=['Per'])
    # p.to_csv('final_features.csv')