# Configuration

In general, you can define any option that you want to use while extracting features or
post-processing data.
You will be able to access them in a `cfg` argument of your [custom
features](/Custom_features.html) and [hooks](./Hooks.html) or in the fields
`self._cfg` and `self._post_config` of
[`FeaturesExtractor`](./API/musif.extract.html#musif.extract.extract.FeaturesExtractor)
and [`DataProcessor`](./API/musif.process.html#musif.process.processor.DataProcessor)
respectively.

However, some options will always be present as they are used by the
stock features and classes. Check the examples to see the definition of all the default
settings:
* [extraction setting example](./Config_extraction_example.html)
* [data processing example](./Config_postprocess_example.html)

To override these options and/or add your own ones, you have two options:
1. Provide to `FeatureExtractor` and `DataProcessor` the file names to YAML files; in
   this case, every YAML variable will become a field in the `Configuration`
   object
2. Provide them a list of key-word arguments, where the key will become the name of the
   field of the `Configuration` object.
You can also mix these two methods and in such a case, the key-word arguments will have
the precedence.

For instance, imagine your YAML file is named `myconf.yml`, and it looks like this:
```yaml
myoption: [1, 2, 3]
```

You could create an extractor object like this:
```python
FeaturesExtractor('myconf.yml', anotheroption="somevalue")
```

Then, in your custom feature, you can access `anotheroption` and `myoption`:
```python
def update_part_objects(
    score_data: dict = None,
    parts_data: list = None,
    cfg: object = None,
    parts_features: list = None,
):
  if cfg.myoption[0] == 1:
    # do something
    pass
  elif cfg.anotheroption == 'somevalue':
    # do something
    pass
```

Also, have a look the [Configuration API page](./API/musif.config.html) to understand how
the `Configuration` class works. You can subclass it for advanced handling of
configurations, see for instance the [Didone feature project](//TODO).
