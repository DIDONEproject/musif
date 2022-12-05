# Tutorial

Musif is a python library that it born as a tool to develop the Didone Project (https://didone.eu/).

The main aim of this project is to try to find which musical features are meaningful in an emotion recognition task.
To do this, a bast amount of musical features (represented in numerical data) are required to run ML and DL algorithms. MusiF is in charge of that.
it is specialized in a 18 century Operas corpus, but intended to work in other registers as well.

To install, just run 'pip install .' inside musiF folder.

Main object of musiF is The FeatureExtractor(), which read scores in xml format and returns a Dataframe containing all info.
Each row represents a score ( or a window of measures if window mode is activated), and each column a feature.

The extractor will extract the features you require and add metadata information to each score's features.

## How to use

### Metadata Information

If you wish to have this metadata included, it has to be placed in form of .csv files in a directory you define in the configuration file (metadata_dir)

These files must have an Id column that will be used to assosiate each metadata file information to each score. This column has to be named the same in every file, obviously, and is defined in the field 'metadata_id_col' of the config file.  

### Corpus files

Files no analyze must be saved in a directory in .xml format. 
Module FileName of basic_modules will extract metadata info from file names, so you can adjust filenames/filenamme module to your will so it does you it's more convenient for your corpora.

### Example program

Checkout    

## Create your own musiF modules