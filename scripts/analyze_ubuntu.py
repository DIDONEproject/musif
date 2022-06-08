import os
import sys
sys.path.insert(0, "../musif")

from musif.extract.extract import FeaturesExtractor
from musif.process.processor import DataProcessor

if __name__ == "__main__":
    # print('\nUpdating metadata files...')
    # os.system("python scripts/metadata_updater.py")
    check_file=None
    # data_dir = r'../Corpus/Half2'
    data_dir = r'../Corpus/xml'
    
    musescore_dir = r'../Corpus/musescore'
    
    name = "features_06_06"
    check_file=name+"_extraction.csv"
    check_file=name+"_first_half.csv"
    
    
    df = FeaturesExtractor("scripts/config_drive.yml", data_dir=data_dir, musescore_dir=musescore_dir, check_file=check_file).extract()
    dest_path=name+"_extraction3.csv"
    df.to_csv(dest_path, index=False)
    k=1
    

