import sys

from musif.extract.features.core.constants import FILE_NAME
import os
from pathlib import Path

import pandas as pd
from feature_extraction.custom_conf import CustomConf
from musif.extract.extract import FeaturesExtractor

from musiF.musif.process.processor import DataProcessor

# MAIN FILE to run extractions of data by Didone Project.

# directory containing xml files
data_dir = Path("data") / "xml"
DEST_PATH = "destination_path"


# directory containing .pkl files in case of previous extractions for cache
cache_dir = None

# csv file containing files which raised error and need to be reextracted
try:
    path_error = f'{DEST_PATH}/error_files.csv'
    errored_files = list(pd.read_csv(path_error, low_memory=False)[FILE_NAME])
except Exception:
    # Handle the case where there is no file is empty
    print("There is no error_files.csv, it will be created and loaded error files are included manually in it.")
    pass


# In case a partial extraction has been run, set here the previous df to avoid re-extracting these files.
# prev_path = str(prefix / NAME) + '.csv'
# exclude_files = list(pd.read_csv('martiser/extractions/total_8_12.csv', low_memory=False)['FileName'])

# In case only some files need to be extracted.
# xml_files = [filename for filename in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, filename)) and filename.endswith('.xml')]
# limit_files = xml_files[0:len(xml_files)//4]

extracted_df = FeaturesExtractor(
    CustomConf("config_extraction_example.yml"),
    data_dir = str(data_dir), 
    # musescore_dir = Path("data") / "musescore", #only for harmonic analysis
    # exclude_files = exclude_files,
    # limit_files = limit_files,
    cache_dir=cache_dir,
).extract()

extracted_df.to_csv(str(DEST_PATH)+'.csv', index=False)

# The raw df will be now saved in the DEST_PATH, and now post-processed
# by the Didone Processor, and ALSO saved in 4 separated csv files.
p = DataProcessor(str(DEST_PATH) + '.csv', "config_postprocess_example.yml")
p.process()

p.data.drop('level_0', axis='columns')
p.save(str(DEST_PATH))
final_name = f'{DEST_PATH}'+'_alldata'+'.csv'

# Running tests to ensure features values make sense 
os.system(f'python tests/test_of_test.py {final_name}')