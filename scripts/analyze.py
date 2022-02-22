import os
import sys
sys.path.insert(0, "../musif")

from musif.extract.extract import FeaturesExtractor

from musif.process.processor import DataProcessor

if __name__ == "__main__":
    # print('\nUpdating metadata files...')
    # os.system("python scripts/metadata_updater.py")
    data_dir = r'../Half_Corpus/xml'
    musescore_dir = r'../../_Ana\Music Analysis/xml/corpus_github/musescore'

    # check_file = 'parsed_files_total.csv'
    check_file=None
    name = "features_new_total"

    # df = FeaturesExtractor("scripts/config_drive.yml", data_dir=data_dir, musescore_dir=musescore_dir, check_file=check_file).extract()
    dest_path=name+"_extraction.csv"
    # df.to_csv(dest_path, index=False)
    DataProcessor("scripts/post_process.yml").process_corpora(dest_path)