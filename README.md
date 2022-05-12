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
 
TODO: which one of the two?

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

    features_df = FeaturesExtractor().extract("scores/xml")

```

### Example 2 - Extract multiple scores features from specific files

```
from musif.extract import FeaturesExtractor

if __name__ == "__main__":

    xml_files = ["scores/xml/score1.xml", "others/score3.xml"]

    features_df = FeaturesExtractor().extract(xml_files, ["obI", "obII"])

```

### Example 3 - Extract single score features

```
from musif.extract import FeaturesExtractor

if __name__ == "__main__":

    features_df = FeaturesExtractor().extract("scores/xml/score1.xml", ["obI", "obII"])

```

### Example 4 - Different Configuration Options

```
from musif.extract import FeaturesExtractor

if __name__ == "__main__":

    features1 = FeaturesExtractor().extract("myfile.xml", ["obI", "obII"])
    features2 = FeaturesExtractor({"split": True, "data_dir": "data"}).extract("myfile.xml", ["obI", "obII"])
    features3 = FeaturesExtractor(split=True, data_dir="data").extract("myfile.xml", ["obI", "obII"])
    features4 = FeaturesExtractor("/home/daniel/clients/didone/projects/musiF/config.yml").extract("myfile.xml", ["obI", "obII"])
    features5 = FeaturesExtractor("config.yml").extract("myfile.xml", ["obI", "obII"])

```

### TODO

[ ] The above examples where put the features?
[ ] The format of the feature file
[ ] Documentation for each single feature
[ ] Detailed comparison with jsymbolic features
[ ] How to add a new custom feature from scratch?
[ ] How to add a new custom feature based on the others?
[ ] Document configuration files
[ ] Various TODO in code (mainly documentation)
[ ] Reformat everything with standard formatting
[ ] Links to the documentation
[ ] Links to related modules
[ ] Links to jupyter notebooks
