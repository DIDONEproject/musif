# Custom features

While using `musiF`, you will be able to add your custom features.

There are 2 different type of features:
* basic features
* generic features

The only true difference among them is that "basic features" will be computed once per
each music score, while "generic features" will be recomputed for each window in the
score. If you disable windows in the [configuration](/Configuration) with the option
`window_size=None`, then there will be no difference. However, "basic features" will be
always computed before of the "generic features".

There are two options in the [configuration](/Configuration) that allow to extend the
features computed:
* `basic_modules_addresses` for extending basic features
* `feature_modules_addresses` for extending generic features

By default, their values will be `["musif.extract.basic_modules"]` and
`["musif.extract.features"]`. To extend them, you have to override their values. By
doing so, you can keep the stock `musiF` features, or completely replace them. For
instance, the following will allow to re-use the stock features; if you omit the
`"musif.extract.basic_modules"`, then the stock features won't be usable anymore.

```yaml
basic_modules_addresses: ["musif.extract.basic_modules", "custom_basic_modules"]
```
Each feature should have two functions `update_part_objects` and
`update_score_objects`. `musiF` will run `update_part_objects` for each part in the score (or
window), and then `update_score_objects` for the score. This is repeated independently
for each score and window.

The two functions have almost the same signature and it is identical for basic and
generic features:
* `score_data` is a dictionary containing all the data loaded from the score or from the
  cache; it contains musescore harmonic annotations and music21 objects. This object
  should **never** be changed, especially if you intend to use the [caching
  system](Caching)
* `part_data` is a dictionary containing data about the part being analysized (for
  `update_part_objects`) or with a list of all the `part_data` (for
  `update_score_objects`). In it, you can find the music21 object of the part, the part
  name, etc. This object should **never** be changed, especially if you intend to use
  the [caching system](Caching)
* `cfg` is a [configuration](/Configuration) object that can be used to access
  configuration options
* `parts_features` is a dictionary with the features already computed for all the
  parts; you should modify this only in `update_part_objects`
* `score_features` is a dictionary with the features already computed for all the
  parts; you should modify this only in `update_score_objects`

In the following we will show 3 different examples of custom features. For starting,
let's create the `custom_features` directory, where we will put all our files: `mkdir
custom_features`.

## 1. Custom feature as a package

If you are going to write a large number of features, you should likely chose this
method. With this method, each feature is implemented as a Python package. This is how
all the `musiF` features are implemented.

First, let's create a directory for the package and a `__init__.py` file in it:
```shell
mkdir custom_features/custom_feature_package 
touch custom_features/custom_feature_package/__init__.py
```

We should now create a module named `handler` inside `custom_feature_package`:
```shell
touch custom_features/custom_feature_package/handler.py
```

`handler.py` will look like this:
```python
def update_score_objects(
    score_data: dict = None,
    parts_data: list = None,
    cfg: object = None,
    parts_features: list = None,
    score_features: dict = None,
):
    print(
        "We are updating stuffs from module inside a package  given its parent package (score)!"
    )
    score_features['OurNewFeature'] = 0


def update_part_objects(
    score_data: dict = None,
    parts_data: list = None,
    cfg: object = None,
    parts_features: list = None,
    score_features: dict = None,
):
    print(
        "We are updating stuffs from module inside a package  given its parent package (part)!"
    )
    parts_features['OurNewFeature'] = 1
```

In the configuration:
```yaml
feature_modules_addresses: 
  - "musif.extract.features"
  - "custom_features"

features:
   - custom_feature_package
```

## 2. Custom feature as a class

If you are writing only a few feature, you may find more confortable with only one file,
instead of a whole directory. For this, you can simply create your module
`costum_feature_module.py`:

```python
class custom_feature_class:
    class handler:
        def update_score_objects(
            self,
            score_data: dict = None,
            parts_data: list = None,
            cfg: object = None,
            parts_features: list = None,
            score_features: dict = None,
        ):
            print(
                "We can even update stuffs from an inner class given a module (score)!"
            )

        def update_part_objects(
            self,
            score_data: dict = None,
            parts_data: list = None,
            cfg: object = None,
            parts_features: list = None,
            score_features: dict = None,
        ):
            print(
                "We can even update stuffs from an inner class given a module (part)!"
            )
```

In the configuration file:
```yaml
feature_modules_addresses: 
  - "musif.extract.features"
  - "custom_feature_module"

features:
   - custom_feature_class
```

If the above code looks weird (with the inner static class and classes having lower
initials), you can also opt for a more object-oriented approach:

```python
class FeatureCreator:
    def __init__(self, feature_type, *args, **kwargs):
      self.handler = feature_type(*args, **kwargs)

class MyNewFeature:
  def __init__(*args, **kwargs):
    pass
    
  def update_score_objects(
      self,
      score_data: dict = None,
      parts_data: list = None,
      cfg: object = None,
      parts_features: list = None,
      score_features: dict = None,
  ):
      print(
          "We can even update stuffs from an inner class given a module (score)!"
      )

  def update_part_objects(
      self,
      score_data: dict = None,
      parts_data: list = None,
      cfg: object = None,
      parts_features: list = None,
      score_features: dict = None,
  ):
      print(
          "We can even update stuffs from an inner class given a module (part)!"
      )

custom_feature_class = FeatureCreator(MyNewFeature, 'other', 'args')
```

## 3. Custom feature as a module

The third option you have actually comes out of the box from the above. You can create a
module inside a package `custom_features/custom_feature_module_in_package.py`:

```python
class handler:
    def update_score_objects(
        self,
        score_data: dict = None,
        parts_data: list = None,
        cfg: object = None,
        parts_features: list = None,
        score_features: dict = None,
    ):
        print(
            "We are updating stuffs from a class inside a module given a package (score)!"
        )

    def update_part_objects(
        self,
        score_data: dict = None,
        parts_data: list = None,
        cfg: object = None,
        parts_features: list = None,
        score_features: dict = None,
    ):
        print(
            "We are updating stuffs from a class inside a module given a package (part)!"
        )
```

And then in the configuration file:
```yaml
feature_modules_addresses: 
  - "musif.extract.features"
  - "custom_features"

features:
   - custom_feature_module_in_package
```
