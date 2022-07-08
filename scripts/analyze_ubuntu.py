import os
import sys
sys.path.insert(0, "../musif")

from musif.extract.extract import FeaturesExtractor
from musif.process.processor import DataProcessor

if __name__ == "__main__":
    # print('\nUpdating metadata files...')
    # os.system("python scripts/metadata_updater.py")
    check_file=None
    data_dir = r'../Corpus/Half'
    data_dir = r'../Corpus/xml/'
    musescore_dir = r'../Corpus/musescore'
    
    prefix = 'martiser/'
    sufix='.csv'
    name = prefix + "extraction_07_07_22"
    dest_path = name + "_extraction"
    check_file = dest_path + ".csv"

    df = FeaturesExtractor("scripts/config_drive.yml", data_dir=data_dir, musescore_dir=musescore_dir, check_file=check_file).extract()
    
    df.to_csv(dest_path+'_2'+sufix, index=False)
    k=1
    

