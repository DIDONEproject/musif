# Workflow
MusiF is a library designed to extract numerical features from scores. Basic class is the FeaturesExtractor(),
which computes all different modules and includes all the info in the final DataFrame.

All public methods inside FeaturesExtractor() are usable separatedly, although the most commong thing to do is to just run 
extract() metod. Similar thing with PostProcessor() class and its process() method.

### How to extract features
To select which features are to be computed, use the configuration file (_.yml file_) or override them when instantiating FeaturesExtractor object.
TO de-select features, just comment them and the'll be skipped. 


The user might want to add their own musical features to be extracted by *musiF*. We'll take a look at this in the next section.
### How to add new features

### Post-process information


### Introduce attributes to Configuration object
