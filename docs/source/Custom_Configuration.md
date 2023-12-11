# Custom Configuration for DIDONE PROJECT
Here we present an example of using ExtracConfiguration class by subclassing it to create our own CustomConf class following specific needs. 

In DIDONE project's case, It was needed to load many *.csv files contatining metadata information and include this inofrmation into the DataFrame that musif extracts. This metadata information loaded in our Custom conf, was later used by our custom modules to include it in the final DataFrame. Check how we inherit parent class 'ExtractConfiguration' and add some customized methods:

## Code
from glob import glob
from os import path

from musif.common._utils import read_dicts_from_csv
from musif.config import ExtractConfiguration


class CustomConf(ExtractConfiguration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._load_metadata()

    def _load_metadata(self) -> None:
        self.scores_metadata = {
            path.basename(file): read_dicts_from_csv(file)
            for file in glob(path.join(self.metadata_dir, "score", "*.csv"))
        }
        if not self.scores_metadata:
            print(
                "\nMetadata could not be loaded properly!! Check metadata path in config file.\n"
            )
        self.characters_gender = read_dicts_from_csv(
            path.join(self.internal_data_dir, "characters_gender.csv")
        )
