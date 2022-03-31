import os
import sys
sys.path.insert(0, "../musif")

from musif.extract.extract import FeaturesExtractor
from musif.process.processor import DataProcessor

if __name__ == "__main__":
    # print('\nUpdating metadata files...')
    # os.system("python scripts/metadata_updater.py")
    
    data_dir = r'../Corpus/xml'
    musescore_dir = r'../Corpus/musescore'
    
    # check_file = 'parsed_files_total.csv'
    name = "features_28_03"
    check_file=name+"_extraction_1.csv"
    df = FeaturesExtractor("scripts/config_drive.yml", data_dir=data_dir, musescore_dir=musescore_dir, check_file=check_file).extract()
    dest_path=name+"_extraction_dynamics2.csv"
    df.to_csv(dest_path, index=False)
    

