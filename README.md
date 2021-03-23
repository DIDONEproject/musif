# musiF

Python library for **Music Feature Extraction and Analysis**, developed by [Didone Project](https://didone.eu/). 

Main goals:

* Extract different kind of features (melodic, harmonics, texture, operatic, ...) from score files
* Reporting & Visualization tools

## Installation

musiF requires:

* Python >= 3.7

We recommend installing it with `pip`:

```bash
git clone https://github.com/DIDONEproject/musiF.git
cd musiF
pip install .
```

## Usage

Assuming we have our scores persisted in a directories structure like this:
 
```
scores                                   others
|                                        |
|__ xml                                  |__ score3.xml
|   |__ score1.xml                       |__ score3.mscx
|   |__ score2.xml                       |
|                                        |__ score4.xml
|__ mscx                                 |__ score4.mscx
    |__ score1.mscx                      
    |__ score2.mscx

```

### Example 1 - Extract multiple scores features from directory

```
from musif.extract import FeaturesExtractor

if __name__ == "__main__":

    features_df = FeaturesExtractor().from_dir("scores/xml", "scores/mscx", ["obI", "obII"])

```

### Example 2 - Extract multiple scores features from specific files

```
from musif.extract import FeaturesExtractor

if __name__ == "__main__":

    xml_files = ["scores/xml/score1.xml", "others/score3.xml"]
    mscx_files = ["scores/mscx/score1.mscx", "others/score3.mscx"]

    features_df = FeaturesExtractor().from_files(xml_files, mscx_files, ["obI", "obII"])

```

### Example 3 - Extract single score features

```
from musif.extract import FeaturesExtractor

if __name__ == "__main__":

    features_df = FeaturesExtractor().from_file("scores/xml/score1.xml", "scores/xml/score1.mscx", ["obI", "obII"])

```

### Example 4 - Different Configuration Options

```
from musif.extract import FeaturesExtractor

if __name__ == "__main__":

    features1 = FeaturesExtractor().from_file("myfile.xml", ["obI", "obII"])
    features2 = FeaturesExtractor({"split": True, "data_dir": "data"}).from_file("myfile.xml", ["obI", "obII"])
    features3 = FeaturesExtractor(split=True, data_dir="data").from_file("myfile.xml", ["obI", "obII"])
    features4 = FeaturesExtractor("/home/daniel/clients/didone/projects/musiF/config.yml").from_file("myfile.xml", ["obI", "obII"])
    features5 = FeaturesExtractor("config.yml").from_file("myfile.xml", ["obI", "obII"])

```

