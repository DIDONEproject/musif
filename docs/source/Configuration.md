# Configuration

In general, you can define any variable for
[`FeaturesExtractor`](./API/musif.extract.html#musif.extract.extract.FeaturesExtractor)
and [`DataProcessor`](./API/musif.process.html#musif.process.processor.DataProcessor).
You will be able to access them in `cfg` argument of your [custom
features](/Custom_features.html) and [hooks](./Caching.html#hooks) or in the fields
`self._cfg` and `self._post_config` of `FeatureExtractor` and `DataProcessor`
respectively.

However, there are some options that will be always present as they are used by the
stock features and classes. Check the examples to see the definition of all the default
settings:
* [extraction setting example](./Config_extraction_example.html)
* [data processing example](./Config_postprocess_example.html)

To override these options and/or add your owns, you have two options:
1. provide to `FeatureExtractor` and `DataProcessor` the file names to yaml files; in
   this case, every yaml variable will become a field in the `Configuration`
   object
2. provide them a list of key-word arguments, where the key will become the name of the
   field of the `Configuration` object.
You can also mix these two methods and in such a case, the key-word arguments will have
the precedence.

Also, have a look the [Configuration API page](./API/musif.config.html) to understand how
the `Configuration` class works. You can subclass it for advanced handling of
configurations, see for instance the [Didone feature project](//TODO).
